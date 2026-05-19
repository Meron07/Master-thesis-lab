import os
import numpy as np

from make_predicted_labels import make_predicted_labels
from make_true_labels import make_true_labels
from evaluate_one_file import compute_metrics


def evaluate_all_runs():
    results = []

    for i in range(1, 11):
        print(f"\nEvaluating run_{i}...")

        csv_file = os.path.expanduser(
            f"~/iec104-lab/results/exp1_6_windows_run_{i}_features.csv"
        )

        predicted_rows = make_predicted_labels(csv_file)
        y_pred = [r["predicted_label"] for r in predicted_rows]

        # These run_i files are baseline repeated runs
        y_true = make_true_labels(csv_file, "exp1_7_noisy_baseline.pcap")

        metrics = compute_metrics(y_true, y_pred)

        print(
            f"Precision={metrics['precision']:.4f}, "
            f"Recall={metrics['recall']:.4f}, "
            f"F1={metrics['f1']:.4f}"
        )

        results.append(metrics)

    return results


def summarize(results):
    precision = [r["precision"] for r in results]
    recall = [r["recall"] for r in results]
    f1 = [r["f1"] for r in results]

    print("\n=== FINAL SUMMARY ===")
    print(f"Precision: mean={np.mean(precision):.4f}, std={np.std(precision):.4f}")
    print(f"Recall:    mean={np.mean(recall):.4f}, std={np.std(recall):.4f}")
    print(f"F1-score:  mean={np.mean(f1):.4f}, std={np.std(f1):.4f}")


if __name__ == "__main__":
    results = evaluate_all_runs()
    summarize(results)
