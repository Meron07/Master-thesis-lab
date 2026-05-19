import argparse
import pandas as pd
from pathlib import Path

def load_df(path: Path):
    df = pd.read_csv(path)
    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch", "tcp.payload"]).copy()
    df = df.sort_values("frame.time_epoch")
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--gap_s", type=float, default=20.0)
    args = ap.parse_args()

    df = load_df(Path(args.test))

    first_seen = {}
    replay_events = []

    for _, row in df.iterrows():
        payload = row["tcp.payload"]
        t = row["frame.time_epoch"]

        if payload in first_seen:
            delta = t - first_seen[payload]
            if delta > args.gap_s:
                replay_events.append((t, delta))
        else:
            first_seen[payload] = t

    print("Payload replay detection completed.")
    print(f"Total payload packets analyzed: {len(df)}")
    print(f"Replay-like payload reappearances: {len(replay_events)}")

    if replay_events:
        print(f"ALARM triggered at time {replay_events[0][0]} (gap={replay_events[0][1]:.2f}s)")
    else:
        print("ALARM not triggered")

if __name__ == "__main__":
    main()
