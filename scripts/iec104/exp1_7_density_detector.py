import argparse
import pandas as pd
from pathlib import Path

ID_COLS = ["ip.src", "ip.dst", "tcp.seq", "tcp.len"]

def load_df(path: Path):
    df = pd.read_csv(path)
    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch"]).copy()
    for c in ID_COLS:
        df[c] = df[c].astype(str)
    df = df.sort_values("frame.time_epoch")
    df["packet_id"] = df[ID_COLS].agg("_".join, axis=1)
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--win_s", type=float, default=10.0)
    ap.add_argument("--step_s", type=float, default=1.0)
    ap.add_argument("--repeat_n", type=int, default=3)
    args = ap.parse_args()

    df = load_df(Path(args.test))

    t0 = df["frame.time_epoch"].min()
    t1 = df["frame.time_epoch"].max()

    win = args.win_s
    step = args.step_s
    start = t0
    alarm_time = None

    while start <= t1:
        end = start + win
        window = df[(df["frame.time_epoch"] >= start) & (df["frame.time_epoch"] < end)]

        counts = window["packet_id"].value_counts()
        max_repeat = counts.max() if len(counts) > 0 else 0

        if max_repeat >= args.repeat_n:
            alarm_time = start
            break

        start += step

    print("Density-based detection completed.")
    print(f"Window size = {args.win_s}s")
    print(f"Repeat threshold = {args.repeat_n}")
    if alarm_time:
        print(f"ALARM triggered at window_start_epoch={alarm_time}")
    else:
        print("ALARM not triggered")

if __name__ == "__main__":
    main()
