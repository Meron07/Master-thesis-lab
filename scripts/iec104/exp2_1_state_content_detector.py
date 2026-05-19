#!/usr/bin/env python3
import argparse
import hashlib
import math
from dataclasses import dataclass
from typing import Optional, Tuple

import pandas as pd


# -------------------------
# IEC-104 parsing helpers
# -------------------------
def hex_to_bytes(hexstr: str) -> bytes:
    if pd.isna(hexstr):
        return b""
    s = str(hexstr).strip().replace(":", "").replace(" ", "")
    if len(s) % 2 != 0:
        return b""
    try:
        return bytes.fromhex(s)
    except ValueError:
        return b""


def sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def parse_apci_i_frame(payload: bytes) -> Optional[Tuple[int, int, bytes]]:
    """
    IEC-104 APCI:
      byte0 = 0x68
      byte1 = length
      bytes2-5 = control field
    I-frame if (control0 & 0x01) == 0
    N(S) = ((control0 + 256*control1) >> 1)
    N(R) = ((control2 + 256*control3) >> 1)
    ASDU starts at byte 6
    """
    if len(payload) < 6:
        return None
    if payload[0] != 0x68:
        return None

    c0, c1, c2, c3 = payload[2], payload[3], payload[4], payload[5]

    # I-frame check
    if (c0 & 0x01) != 0:
        return None

    ns = ((c1 << 8) | c0) >> 1
    nr = ((c3 << 8) | c2) >> 1
    asdu = payload[6:]
    return ns, nr, asdu


# -------------------------
# Detection logic
# -------------------------
@dataclass
class Config:
    gap_s: float
    window_s: int
    seq_mod: int
    max_step: int
    jump_k: int
    rare_max_count: int
    rep_density_threshold: int
    score_threshold: int

    w_backward: int
    w_jump: int
    w_stale: int
    w_rep: int


def modular_delta(curr: int, prev: int, mod: int) -> int:
    """Return (curr - prev) mod mod in range [0, mod-1]."""
    return (curr - prev) % mod


def compute_session_flags(df_i: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """
    Adds:
      backward_ns, jump_ns
    Uses modular arithmetic to handle wrap-around.
    Allows small forward increments up to max_step.
    Flags big forward jumps (delta > jump_k).
    Flags large "backward" moves when delta is very large (close to mod).
    """
    df_i = df_i.sort_values(["tcp.stream", "time_epoch"]).reset_index(drop=True)

    df_i["backward_ns"] = False
    df_i["jump_ns"] = False

    # Optional retransmission mitigation: drop exact duplicate N(S) per stream (keep first)
    # This removes many duplicates caused by retransmissions.
    df_i = df_i.drop_duplicates(subset=["tcp.stream", "ns"], keep="first").copy()

    for stream_id, g in df_i.groupby("tcp.stream", sort=False):
        idx = g.index.tolist()
        ns_list = g["ns"].astype(int).tolist()

        prev = None
        for k, row_i in enumerate(idx):
            curr = ns_list[k]
            if prev is None:
                prev = curr
                continue

            d = modular_delta(curr, prev, cfg.seq_mod)

            # d == 0: duplicate (already mostly removed), ignore
            if d == 0:
                prev = curr
                continue

            # Normal: small forward progress (1..max_step)
            if 1 <= d <= cfg.max_step:
                prev = curr
                continue

            # Wrap-around is naturally handled because if prev near mod-1 and curr small,
            # d will be small. So it won't land here.
            # Big forward jump
            if d > cfg.jump_k and d < (cfg.seq_mod - cfg.max_step):
                df_i.at[row_i, "jump_ns"] = True
                prev = curr
                continue

            # Large delta close to mod means curr is behind prev (backward movement)
            # Example: prev=2000 curr=1800 => d = mod-200 -> large
            if d >= (cfg.seq_mod - cfg.max_step):
                # small backward wiggle allowed (<= max_step) already excluded,
                # so this is significant backward.
                df_i.at[row_i, "backward_ns"] = True

            prev = curr

    return df_i


def compute_asdu_staleness(df_i: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """
    Adds:
      asdu_fp, fp_age_s, stale_fp
      repeat_fp_count, high_rep_density

    Key idea:
      stale_fp only triggers when:
        - fingerprint is rare (<= rare_max_count within that stream), AND
        - it reappears after gap_s seconds
    This avoids baseline exploding on periodic measurements.
    """
    df_i["asdu_fp"] = df_i["asdu_bytes"].apply(sha1_hex)

    # rarity per stream
    counts = (
        df_i.groupby("tcp.stream")["asdu_fp"]
        .value_counts()
        .rename("fp_total_count")
        .reset_index()
    )
    df_i = df_i.merge(counts, on=["tcp.stream", "asdu_fp"], how="left")
    df_i["fp_total_count"] = df_i["fp_total_count"].fillna(0).astype(int)
    df_i["is_rare_fp"] = df_i["fp_total_count"] <= cfg.rare_max_count

    first_seen = {}  # (stream, fp) -> first time
    df_i["stale_fp"] = False
    df_i["fp_age_s"] = 0.0

    for i, row in df_i.iterrows():
        key = (int(row["tcp.stream"]), row["asdu_fp"])
        t = float(row["time_epoch"])
        if key not in first_seen:
            first_seen[key] = t
            continue

        age = t - first_seen[key]
        df_i.at[i, "fp_age_s"] = age

        if age >= cfg.gap_s and bool(row["is_rare_fp"]):
            df_i.at[i, "stale_fp"] = True

    # repetition density per stream+window
    df_i["window_id"] = (df_i["time_epoch"] // cfg.window_s).astype(int)

    rep_counts = (
        df_i.groupby(["tcp.stream", "window_id"])["asdu_fp"]
        .apply(lambda s: int(s.duplicated().sum()))
        .rename("repeat_fp_count")
        .reset_index()
    )
    df_i = df_i.merge(rep_counts, on=["tcp.stream", "window_id"], how="left")
    df_i["repeat_fp_count"] = df_i["repeat_fp_count"].fillna(0).astype(int)
    df_i["high_rep_density"] = df_i["repeat_fp_count"] >= cfg.rep_density_threshold

    return df_i


def score_windows(df_i: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    def score_window(g: pd.DataFrame) -> pd.Series:
        score = 0
        reasons = []

        if g["backward_ns"].any():
            score += cfg.w_backward
            reasons.append("backward_ns")
        if g["jump_ns"].any():
            score += cfg.w_jump
            reasons.append("jump_ns")
        if g["stale_fp"].any():
            score += cfg.w_stale
            reasons.append("stale_fp")
        if g["high_rep_density"].any():
            score += cfg.w_rep
            reasons.append("high_rep_density")

        return pd.Series(
            {
                "score": score,
                "reasons": ",".join(reasons) if reasons else "",
                "packets": int(len(g)),
                "stale_count": int(g["stale_fp"].sum()),
                "backward_count": int(g["backward_ns"].sum()),
                "jump_count": int(g["jump_ns"].sum()),
                "repeat_fp_count": int(g["repeat_fp_count"].max()) if "repeat_fp_count" in g else 0,
                "alarm": bool(score >= cfg.score_threshold),
            }
        )

    windows = (
        df_i.groupby(["tcp.stream", "window_id"])
        .apply(score_window)
        .reset_index()
    )

    windows["window_start_epoch"] = windows["window_id"] * cfg.window_s
    windows["window_end_epoch"] = windows["window_start_epoch"] + cfg.window_s
    return windows


# -------------------------
# Main
# -------------------------
def main():
    ap = argparse.ArgumentParser(description="IEC-104 state + content replay detector (no ML).")
    ap.add_argument("--input", required=True, help="Input CSV (payload stream export).")
    ap.add_argument("--out-flags", required=True, help="Output CSV for packet-level flags.")
    ap.add_argument("--out-windows", required=True, help="Output CSV for window-level scores.")
    ap.add_argument("--time-col", default="frame.time_epoch", help="Time column in CSV (default: frame.time_epoch).")

    # Tuning knobs (sane defaults for baseline not to explode)
    ap.add_argument("--gap-s", type=float, default=60.0)
    ap.add_argument("--window-s", type=int, default=10)
    ap.add_argument("--seq-mod", type=int, default=32768)  # 15-bit seq space typical
    ap.add_argument("--max-step", type=int, default=5)
    ap.add_argument("--jump-k", type=int, default=200)
    ap.add_argument("--rare-max-count", type=int, default=2)
    ap.add_argument("--rep-density-th", type=int, default=5)
    ap.add_argument("--score-th", type=int, default=5)
    ap.add_argument("--stream-mode", choices=["tcpstream", "ippair"], default="tcpstream",
                help="How to group sessions. tcpstream requires tcp.stream. ippair uses ip.src+ip.dst.")

    args = ap.parse_args()

    cfg = Config(
        gap_s=args.gap_s,
        window_s=args.window_s,
        seq_mod=args.seq_mod,
        max_step=args.max_step,
        jump_k=args.jump_k,
        rare_max_count=args.rare_max_count,
        rep_density_threshold=args.rep_density_th,
        score_threshold=args.score_th,
        w_backward=3,
        w_jump=2,
        w_stale=2,
        w_rep=1,
    )

    df = pd.read_csv(args.input)

    required = {args.time_col, "tcp.payload"}
    if args.stream_mode == "tcpstream":
       required.add("tcp.stream")
    else:
       required |= {"ip.src", "ip.dst"}

    missing = required - set(df.columns)
    if missing:
       raise ValueError(f"Missing columns in CSV: {missing}")

    df = df.copy()
    df["time_epoch"] = pd.to_numeric(df[args.time_col], errors="coerce")
    if args.stream_mode == "tcpstream":
       df["tcp.stream"] = pd.to_numeric(df["tcp.stream"], errors="coerce")
    else:
    # Build a stable pseudo-stream id from (ip.src, ip.dst)
       pairs = df["ip.src"].astype(str) + "->" + df["ip.dst"].astype(str)
       df["tcp.stream"] = pd.factorize(pairs)[0]
    df = df.dropna(subset=["time_epoch", "tcp.stream", "tcp.payload"])

    df["payload_bytes"] = df["tcp.payload"].apply(hex_to_bytes)

    parsed = df["payload_bytes"].apply(parse_apci_i_frame)
    df["is_i_frame"] = parsed.notna()

    df_i = df[df["is_i_frame"]].copy()
    df_i[["ns", "nr", "asdu_bytes"]] = pd.DataFrame(
        parsed[df["is_i_frame"]].tolist(),
        index=df_i.index
    )

    # Session consistency + content staleness
    df_i = compute_session_flags(df_i, cfg)
    df_i = compute_asdu_staleness(df_i, cfg)

    windows = score_windows(df_i, cfg)

    # Save outputs
    df_i.to_csv(args.out_flags, index=False)
    windows.to_csv(args.out_windows, index=False)

    # Print alarm windows
    alarms = windows[windows["alarm"]].sort_values(["tcp.stream", "window_id"])
    print("\n=== ALARM WINDOWS ===")
    if len(alarms) == 0:
        print("No alarms.")
    else:
        print(
            alarms[
                ["tcp.stream", "window_start_epoch", "window_end_epoch", "score", "reasons"]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
