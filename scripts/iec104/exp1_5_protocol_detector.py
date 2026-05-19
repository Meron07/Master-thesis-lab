import argparse
import pandas as pd
from pathlib import Path

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna()
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, help="Feature CSV to analyze")
    args = ap.parse_args()

    test_path = Path(args.test).expanduser()
    df = load_csv(test_path)

    # Define a simple packet identity (excluding time)
    df["packet_id"] = (
        df["ip.src"].astype(str) + "_" +
        df["ip.dst"].astype(str) + "_" +
        df["tcp.seq"].astype(str) + "_" +
        df["tcp.len"].astype(str)
    )

    duplicate_counts = df["packet_id"].value_counts()
    duplicates = duplicate_counts[duplicate_counts > 1]

    print("Protocol-Aware Detection Completed")
    print(f"Total packets analyzed: {len(df)}")
    print(f"Unique packet patterns: {df['packet_id'].nunique()}")
    print(f"Duplicate packet patterns: {len(duplicates)}")

    if len(duplicates) > 0:
        print("\nTop duplicated packet patterns:")
        print(duplicates.head())

if __name__ == "__main__":
    main()
