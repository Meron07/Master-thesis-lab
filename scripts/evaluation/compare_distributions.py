import csv
import os
import numpy as np


def load_values(file_path):
    values = []
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            row = {k.strip(): v for k, v in row.items()}
            values.append(int(row["suspicious_count"]))
    return values


if __name__ == "__main__":
    baseline_file = os.path.expanduser(
        "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_baseline_features.csv"
    )

    replay_file = os.path.expanduser(
        "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_replay_features.csv"
    )

    baseline = load_values(baseline_file)
    replay = load_values(replay_file)

    print("Baseline stats:")
    print(f"Mean: {np.mean(baseline):.2f}")
    print(f"Min: {min(baseline)}, Max: {max(baseline)}")

    print("\nReplay stats:")
    print(f"Mean: {np.mean(replay):.2f}")
    print(f"Min: {min(replay)}, Max: {max(replay)}")

    print("\nDifference (Replay - Baseline mean):")
    print(f"{np.mean(replay) - np.mean(baseline):.2f}")
