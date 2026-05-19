import argparse
import pandas as pd
from pathlib import Path

ID_COLS = ["ip.src", "ip.dst", "tcp.seq", "tcp.len"]


def load_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Clean column names
    df.columns = [str(c).strip().replace('"', "") for c in df.columns]

    needed = ["frame.time_epoch"] + ID_COLS
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")

    # Clean and convert time column
    df["frame.time_epoch"] = (
        df["frame.time_epoch"]
        .astype(str)
        .str.replace('"', '', regex=False)
        .str.strip()
    )
    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch"]).copy()

    # Clean ID columns
    for c in ID_COLS:
        df[c] = (
            df[c]
            .astype(str)
            .str.replace('"', '', regex=False)
            .str.strip()
        )

    df = df.sort_values("frame.time_epoch").reset_index(drop=True)

    # Build stable packet id explicitly
    df["packet_id"] = (
        df["ip.src"] + "_" +
        df["ip.dst"] + "_" +
        df["tcp.seq"] + "_" +
        df["tcp.len"]
    )

    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, help="Baseline feature CSV")
    ap.add_argument("--test", required=True, help="Test feature CSV")
    ap.add_argument(
        "--gap_s",
        type=float,
        default=10.0,
        help="Flag reappearance if >= this many seconds since baseline first seen",
    )
    ap.add_argument("--win_s", type=float, default=10.0, help="Sliding window size in seconds")
    ap.add_argument("--step_s", type=float, default=1.0, help="Window step in seconds")
    ap.add_argument("--alarm_n", type=int, default=5, help="Raise alarm if suspicious_count >= this per window")
    ap.add_argument("--outdir", default=str(Path.home() / "iec104-lab/results"), help="Output directory")
    args = ap.parse_args()

    baseline_path = Path(args.baseline).expanduser()
    test_path = Path(args.test).expanduser()
    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    base = load_df(baseline_path)
    test = load_df(test_path)

    # Baseline first-seen times for each pattern
    base_first = base.groupby("packet_id")["frame.time_epoch"].min()

    # Join baseline first-seen into test rows
    test = test.join(base_first.rename("base_first_seen"), on="packet_id")
    known = test.dropna(subset=["base_first_seen"]).copy()
    known["delta_from_base_first"] = known["frame.time_epoch"] - known["base_first_seen"]

    # Suspicious events are reappearances far after baseline first seen
    known["is_suspicious"] = known["delta_from_base_first"] >= args.gap_s

    if len(test) == 0:
        raise ValueError("Test file has 0 rows after parsing.")

    t0 = test["frame.time_epoch"].min()
    t1 = test["frame.time_epoch"].max()

    rows = []
    alarm_time = None

    win = args.win_s
    step = args.step_s
    start = t0

    susp = known[known["is_suspicious"]].copy()
    susp_times = susp["frame.time_epoch"].to_numpy()
    susp_ids = susp["packet_id"].to_numpy()

    while start <= t1:
        end = start + win

        if len(susp) == 0:
            susp_count = 0
            unique_patterns = 0
        else:
            mask = (susp_times >= start) & (susp_times < end)
            susp_count = int(mask.sum())
            unique_patterns = int(pd.Series(susp_ids[mask]).nunique()) if susp_count > 0 else 0

        rows.append(
            {
                "window_start_epoch": start,
                "window_end_epoch": end,
                "suspicious_count": susp_count,
                "unique_suspicious_patterns": unique_patterns,
            }
        )

        if alarm_time is None and susp_count >= args.alarm_n:
            alarm_time = start

        start += step

    out_csv = outdir / f"exp1_6_windows_{test_path.stem}.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    out_txt = outdir / f"exp1_6_alarm_{test_path.stem}.txt"
    with open(out_txt, "w") as f:
        f.write("Experiment 1.6 - Sliding-window detection\n\n")
        f.write(f"Baseline: {baseline_path}\n")
        f.write(f"Test:     {test_path}\n\n")
        f.write(f"gap_s   = {args.gap_s}\n")
        f.write(f"win_s   = {args.win_s}\n")
        f.write(f"step_s  = {args.step_s}\n")
        f.write(f"alarm_n = {args.alarm_n}\n\n")
        if alarm_time is None:
            f.write("ALARM: not triggered\n")
        else:
            f.write(f"ALARM: triggered at window_start_epoch={alarm_time}\n")
        f.write(f"\nSaved window timeline: {out_csv}\n")

    print("Sliding-window detection completed.")
    print(f"Saved: {out_csv}")
    print(f"Saved: {out_txt}")
    if alarm_time is None:
        print("ALARM: not triggered")
    else:
        print(f"ALARM: triggered at window_start_epoch={alarm_time}")


if __name__ == "__main__":
    main()
