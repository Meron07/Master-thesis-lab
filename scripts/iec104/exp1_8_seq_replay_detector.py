import argparse
import pandas as pd
from pathlib import Path

def load_df(path: Path):
    df = pd.read_csv(path)
    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch"]).copy()
    df = df.sort_values("frame.time_epoch")
    df["packet_id"] = (
        df["ip.src"].astype(str) + "_" +
        df["ip.dst"].astype(str) + "_" +
        df["tcp.seq"].astype(str)
    )
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    args = ap.parse_args()

    df = load_df(Path(args.test))

    seen = set()
    replays = []

    for _, row in df.iterrows():
        pid = row["packet_id"]
        if pid in seen:
            replays.append(row["frame.time_epoch"])
        else:
            seen.add(pid)

    print("Sequence replay detection completed.")
    print(f"Total packets analyzed: {len(df)}")
    print(f"Replayed sequence occurrences: {len(replays)}")

    if len(replays) > 0:
        print(f"ALARM triggered at first replay time: {replays[0]}")
    else:
        print("ALARM not triggered")

if __name__ == "__main__":
    main()
