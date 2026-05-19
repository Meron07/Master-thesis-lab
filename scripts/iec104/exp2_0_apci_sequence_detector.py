import argparse
import pandas as pd
from pathlib import Path

def parse_ns_nr(payload_hex: str):
    if not isinstance(payload_hex, str):
        return None, None

    payload_hex = payload_hex.replace(":", "").strip()
    if len(payload_hex) < 12:
        return None, None

    try:
        b = bytes.fromhex(payload_hex)
    except Exception:
        return None, None

    # IEC-104 APCI start byte
    if len(b) < 6 or b[0] != 0x68:
        return None, None

    apdu_len = b[1]  # length after 0x68
    if apdu_len < 4:
        return None, None

    # Require full APDU in this TCP payload chunk
    if len(b) < 2 + apdu_len:
        return None, None

    # Only parse I-frames:
    # I-frame if bit0 of byte2 is 0
    if (b[2] & 0x01) != 0:
        return None, None

    ns = ((b[3] << 8) | b[2]) >> 1
    nr = ((b[5] << 8) | b[4]) >> 1
    return ns, nr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, help="CSV with frame.time_epoch,tcp.stream,ip.src,ip.dst,tcp.len,tcp.payload")
    ap.add_argument("--outdir", default=str(Path.home() / "iec104-lab/results"), help="Output directory")
    ap.add_argument("--tag", default=None, help="Optional tag used in output filenames (default: input stem)")
    args = ap.parse_args()

    test_path = Path(args.test).expanduser()
    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(test_path)

    needed = {"frame.time_epoch", "tcp.stream", "ip.src", "ip.dst", "tcp.payload"}
    missing = sorted(list(needed - set(df.columns)))
    if missing:
        raise ValueError(f"Missing columns in {test_path}: {missing}")

    df["frame.time_epoch"] = pd.to_numeric(df["frame.time_epoch"], errors="coerce")
    df = df.dropna(subset=["frame.time_epoch", "tcp.payload"]).copy()
    df = df.sort_values("frame.time_epoch").reset_index(drop=True)

    tag = args.tag or test_path.stem

    last_ns = {}  # key -> last ns
    anomaly_rows = []
    parsed_count = 0

    for _, row in df.iterrows():
        key = (int(row["tcp.stream"]), str(row["ip.src"]), str(row["ip.dst"]))
        t = float(row["frame.time_epoch"])

        ns, nr = parse_ns_nr(row["tcp.payload"])
        if ns is None:
            continue

        parsed_count += 1

        prev = last_ns.get(key)
        if prev is not None:
            # ignore duplicates (likely retransmissions)
            if ns < prev:
                anomaly_rows.append({
                    "time_epoch": t,
                    "tcp.stream": key[0],
                    "ip.src": key[1],
                    "ip.dst": key[2],
                    "ns_prev": prev,
                    "ns_curr": ns,
                    "delta_ns": ns - prev,
                    "nr_curr": nr,
                    "anomaly_type": "backward_ns"
                })

        last_ns[key] = ns

    anomalies_df = pd.DataFrame(anomaly_rows)

    anomalies_csv = outdir / f"exp2_0_apci_anomalies_{tag}.csv"
    anomalies_df.to_csv(anomalies_csv, index=False)

    # Summary
    summary_txt = outdir / f"exp2_0_apci_summary_{tag}.txt"
    with open(summary_txt, "w") as f:
        f.write("Experiment 2.0 — IEC-104 APCI I-frame Sequence Validation\n\n")
        f.write(f"Input: {test_path}\n")
        f.write(f"Parsed valid I-frames: {parsed_count}\n")
        f.write(f"Backward N(S) anomalies: {len(anomalies_df)}\n")
        if len(anomalies_df) > 0:
            f.write(f"First anomaly time_epoch: {anomalies_df.iloc[0]['time_epoch']}\n")
            per_stream = anomalies_df.groupby("tcp.stream").size().sort_values(ascending=False)
            f.write("\nAnomalies per tcp.stream (top 10):\n")
            f.write(per_stream.head(10).to_string())
            f.write("\n")
        f.write(f"\nSaved anomalies CSV: {anomalies_csv}\n")

    print("APCI sequence validation completed.")
    print(f"Parsed valid I-frames: {parsed_count}")
    print(f"Backward N(S) anomalies: {len(anomalies_df)}")
    print(f"Saved: {anomalies_csv}")
    print(f"Saved: {summary_txt}")

    if len(anomalies_df) > 0:
        print(f"ALARM triggered (first anomaly at time_epoch={anomalies_df.iloc[0]['time_epoch']})")
    else:
        print("ALARM not triggered")

if __name__ == "__main__":
    main()
