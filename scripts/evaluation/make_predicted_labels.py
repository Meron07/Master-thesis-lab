import csv
import os


def make_predicted_labels(input_csv):
    rows = []

    with open(input_csv, "r", newline="") as f:
        reader = csv.DictReader(f)

        # Normalize column names (remove spaces)
        fieldnames = [name.strip() for name in reader.fieldnames]
        reader.fieldnames = fieldnames

        print("Detected columns:", fieldnames)

        for row in reader:
            # clean row keys
            row = {k.strip(): v for k, v in row.items()}

            suspicious_count = int(row["suspicious_count"])

            predicted_label = 1 if suspicious_count >=5 else 0

            rows.append({
                "window_start": row.get("window_start_epoch"),
                "window_end": row.get("window_end_epoch"),
                "epochs": row.get("epochs"),
                "suspicious_count": suspicious_count,
                "unique_suspicious_patterns": int(row["unique_suspicious_patterns"]),
                "predicted_label": predicted_label
            })

    return rows


if __name__ == "__main__":
    input_file = os.path.expanduser(
        "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_replay_features.csv"
    )

    results = make_predicted_labels(input_file)

    print("\nFirst 10 predicted labels:")
    for row in results[:10]:
        print(
            f"{row['window_start']} -> suspicious_count={row['suspicious_count']} "
            f"-> predicted_label={row['predicted_label']}"
        )

    total_windows = len(results)
    alarms = sum(r["predicted_label"] for r in results)

    print(f"\nTotal windows: {total_windows}")
    print(f"Predicted attack windows: {alarms}")
    print(f"Predicted normal windows: {total_windows - alarms}")
