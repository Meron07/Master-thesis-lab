import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="GOOSE replay detector based on repeated (stNum, sqNum) pairs")
parser.add_argument("--input_csv", required=True, help="Path to input GOOSE CSV")
parser.add_argument("--output_csv", required=True, help="Path to output CSV with replay alerts")
args = parser.parse_args()

df = pd.read_csv(args.input_csv)

seen = {}
alerts = []

for _, r in df.iterrows():
    stream = r["goose.gocbRef"]
    st = r["goose.stNum"]
    sq = r["goose.sqNum"]

    if stream not in seen:
        seen[stream] = set()

    key = (st, sq)

    if key in seen[stream]:
        alerts.append(1)
    else:
        alerts.append(0)
        seen[stream].add(key)

df["replay_alert"] = alerts
df.to_csv(args.output_csv, index=False)

print("Replay alerts:", sum(alerts))
print("Saved to:", args.output_csv)
