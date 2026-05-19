import os
import numpy as np

from make_predicted_labels import make_predicted_labels
from make_true_labels import make_true_labels
from evaluate_one_file import compute_metrics


def evaluate_all_runs():
    results = []

    for i in range(1, 11):
        print(f"\nEvaluating replay run_{i}...")

        csv_file = os.path.expanduser(
            f"~/iec104-lab/multi_runs_real/results/replay/exp1_6_windows_run_{i}_features.csv"
        )

        predicted_rows = make_predicted_labels(csv_file)
        y_pred = [r["predicted_label"] for r in predicted_rows]

        y_true = make_true_labels(csv_file, "exp1_7_noisy_replay.pcap")

        metrics = compute_metrics(y_true, y_pred)

        print(
            f"TP={metrics['tp']}, FN={metrics['fn']}, "
            f"Precision={metrics['precision']:.4f}, "
            f"Recall={metrics['recall']:.4f}, "
            f"F1={metrics['f1']:.4f}"
        )

        results.append(metrics)

    return results


def summarize(results):
    tps = [r["tp"] for r in results]
    fns = [r["fn"] for r in results]
    precisions = [r["precision"] for r in results]
    recalls = [r["recall"] for r in results]
    f1s = [r["f1"] for r in results]

    print("\n=== REPLAY FINAL SUMMARY ===")
    print(f"TP:        mean={np.mean(tps):.4f}, std={np.std(tps):.4f}")
    print(f"FN:        mean={np.mean(fns):.4f}, std={np.std(fns):.4f}")
    print(f"Precision: mean={np.mean(precisions):.4f}, std={np.std(precisions):.4f}")
    print(f"Recall:    mean={np.mean(recalls):.4f}, std={np.std(recalls):.4f}")
    print(f"F1-score:  mean={np.mean(f1s):.4f}, std={np.std(f1s):.4f}")


if __name__ == "__main__":
    results = evaluate_all_runs()
    summarize(results)
