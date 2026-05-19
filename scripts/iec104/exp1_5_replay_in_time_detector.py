import argparse
import pandas as pd
from pathlib import Path

ID_COLS = ["ip.src", "ip.dst", "tcp.seq", "tcp.len"]

def load_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    needed = ["frame.time_epoch"] + ID_COLS
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {path}: {missing}")

    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    for c in ID_COLS:
        df[c] = df[c].astype(str)

    df = df.dropna(subset=["frame.time_epoch"]).sort_values("frame.time_epoch")
    df["packet_id"] = df[ID_COLS].agg("_".join, axis=1)
    return df
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, help="Baseline feature CSV")
    ap.add_argument("--test", required=True, help="Test feature CSV (mimic replay capture)")
    ap.add_argument("--gap_s", type=float, default=10.0, help="Min time gap (seconds) to flag reappearance")
    ap.add_argument("--outdir", default=str(Path.home() / "iec104-lab/results"), help="Output directory")
    args = ap.parse_args()

    baseline_path = Path(args.baseline).expanduser()
    test_path = Path(args.test).expanduser()
    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    base = load_df(baseline_path)
    test = load_df(test_path)

    # Build baseline "first seen" times for packet patterns
    base_first = base.groupby("packet_id")["frame.time_epoch"].min()

    # In the test, find packet_ids that existed in baseline
    test = test.join(base_first.rename("base_first_seen"), on="packet_id")

    # Only consider patterns that existed in baseline (since you replayed from baseline)
    known = test.dropna(subset=["base_first_seen"]).copy()

    # Time since first appearance in baseline
    known["delta_from_baseline_first"] = known["frame.time_epoch"] - known["base_first_seen"]

    # Flag if the same packet_id appears "too late" relative to baseline first seen
    suspicious = known[known["delta_from_baseline_first"] >= args.gap_s].copy()

    # Summaries
    total_test = len(test)
    total_known = len(known)
    total_susp = len(suspicious)
    unique_susp_ids = suspicious["packet_id"].nunique()

 
   # Save suspicious rows for evidence
    suspicious_out = outdir / f"exp1_5_suspicious_{test_path.stem}.csv"
    suspicious[["frame.time_epoch", "packet_id", "delta_from_baseline_first"]].to_csv(suspicious_out, index=False)

    summary_out = outdir / f"exp1_5_summary_{test_path.stem}.txt"
    with open(summary_out, "w") as f:
        f.write("Experiment 1.5 — Replay-in-time Detection Summary\n\n")
        f.write(f"Baseline: {baseline_path}\n")
        f.write(f"Test:     {test_path}\n")
        f.write(f"Gap threshold: {args.gap_s:.1f} seconds\n\n")
        f.write(f"Total packets (test): {total_test}\n")
        f.write(f"Packets matching baseline patterns: {total_known}\n")
        f.write(f"Suspicious reappearances: {total_susp}\n")
        f.write(f"Unique suspicious packet patterns: {unique_susp_ids}\n\n")
        if total_susp:
            f.write("Top repeated suspicious patterns (count):\n")
            f.write(str(suspicious["packet_id"].value_counts().head(10)))
            f.write("\n")

    print("Replay-in-time detection completed.")
    print(f"Gap threshold = {args.gap_s:.1f}s")
    print(f"Suspicious reappearances = {total_susp}")
    print(f"Unique suspicious patterns = {unique_susp_ids}")
    print(f"Saved: {summary_out}")
    print(f"Saved: {suspicious_out}")

if __name__ == "__main__":
    main()
