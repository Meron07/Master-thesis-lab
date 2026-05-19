import argparse
import pandas as pd
from pathlib import Path

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "frame.time_epoch" not in df.columns:
        raise ValueError(f"Missing column 'frame.time_epoch' in {path}")
    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch"]).sort_values("frame.time_epoch")
    df["iat"] = df["frame.time_epoch"].diff()
    df = df.dropna(subset=["iat"])
    return df
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, help="Baseline timing CSV (frame.time_epoch)")
    ap.add_argument("--test", required=True, help="Test timing CSV to evaluate")
    ap.add_argument("--out", default=str(Path.home() / "iec104-lab/results"), help="Output directory")
    args = ap.parse_args()

    baseline_path = Path(args.baseline).expanduser()
    test_path = Path(args.test).expanduser()
    outdir = Path(args.out).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    baseline = load_csv(baseline_path)
    test = load_csv(test_path)

    p01 = baseline["iat"].quantile(0.01)
    p99 = baseline["iat"].quantile(0.99)

    test["flag"] = "normal"
    test.loc[test["iat"] < p01, "flag"] = "too_fast_vs_baseline"
    test.loc[test["iat"] > p99, "flag"] = "too_slow_vs_baseline"

    anoms = test[test["flag"] != "normal"]

    summary_path = outdir / f"timing_summary_{test_path.stem}.txt"
    with open(summary_path, "w") as f:
        f.write("Timing-Based Detection Summary\n\n")
        f.write(f"Baseline: {baseline_path}\n")
        f.write(f"Test:     {test_path}\n\n")
        f.write(f"Lower threshold (p01): {p01:.9f} s\n")
        f.write(f"Upper threshold (p99): {p99:.9f} s\n\n")
        f.write(f"Test packets analyzed: {len(test)}\n")
        f.write(f"Anomalies found:       {len(anoms)}\n\n")
        f.write("Counts by type:\n")
        f.write(str(anoms["flag"].value_counts()))
        f.write("\n")

    print("Detection completed.")
    print(f"p01 = {p01:.9f}s")
    print(f"p99 = {p99:.9f}s")
    print(f"Anomalies detected = {len(anoms)}")
    print(f"Saved: {summary_path}")

if __name__ == "__main__":
    main()
