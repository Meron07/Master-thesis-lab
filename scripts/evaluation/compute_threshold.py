import csv
import os
import numpy as np


def load_suspicious_counts(file_path):
    values = []
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)

        # clean headers
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            row = {k.strip(): v for k, v in row.items()}
            values.append(int(row["suspicious_count"]))

    return values


if __name__ == "__main__":
    baseline_file = os.path.expanduser(
        "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_baseline_features.csv"
    )

    values = load_suspicious_counts(baseline_file)

    mean = np.mean(values)
    std = np.std(values)
    threshold = mean + 3 * std

    print("Baseline statistics:")
    print(f"Mean: {mean:.2f}")
    print(f"Std: {std:.2f}")
    print(f"Threshold (mean + 3*std): {threshold:.2f}")

    print("\nMin / Max:")
    print(f"Min: {min(values)}")
    print(f"Max: {max(values)}")
