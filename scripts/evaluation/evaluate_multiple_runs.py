import os
import numpy as np
from make_predicted_labels import make_predicted_labels
from make_true_labels import make_true_labels
from evaluate_one_file import compute_metrics


def evaluate_runs(folder, label_name):
    results = []

    for i in range(1, 11):
        file_path = os.path.join(folder, f"run_{i}.pcap")

        # corresponding CSV (you will adapt if needed)
        csv_file = os.path.expanduser(
            "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_baseline_features.csv"
        )

        predicted_rows = make_predicted_labels(csv_file)
        y_pred = [r["predicted_label"] for r in predicted_rows]

        y_true = make_true_labels(csv_file, label_name)

        metrics = compute_metrics(y_true, y_pred)
        results.append(metrics)

        print(f"Run {i}: Precision={metrics['precision']:.3f}, Recall={metrics['recall']:.3f}")

    return results


def summarize(results):
    precision = [r["precision"] for r in results]
    recall = [r["recall"] for r in results]
    f1 = [r["f1"] for r in results]

    print("\n=== Summary ===")
    print(f"Precision: mean={np.mean(precision):.3f}, std={np.std(precision):.3f}")
    print(f"Recall:    mean={np.mean(recall):.3f}, std={np.std(recall):.3f}")
    print(f"F1-score:  mean={np.mean(f1):.3f}, std={np.std(f1):.3f}")


if __name__ == "__main__":
    folder = os.path.expanduser("~/iec104-lab/multi_runs/noisy_baseline")
    label_name = "exp1_7_noisy_baseline.pcap"

    results = evaluate_runs(folder, label_name)
    summarize(results)
