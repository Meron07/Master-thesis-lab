import os
import numpy as np

from make_predicted_labels import make_predicted_labels
from make_true_labels import make_true_labels
from evaluate_one_file import compute_metrics


def evaluate_all_runs():
    results = []

    for i in range(1, 11):
        print(f"\nEvaluating baseline run_{i}...")

        csv_file = os.path.expanduser(
            f"~/iec104-lab/multi_runs_real/results/exp1_6_windows_run_{i}_features.csv"
        )

        predicted_rows = make_predicted_labels(csv_file)
        y_pred = [r["predicted_label"] for r in predicted_rows]

        y_true = make_true_labels(csv_file, "exp1_7_noisy_baseline.pcap")

        metrics = compute_metrics(y_true, y_pred)

        fp = metrics["fp"]
        tn = metrics["tn"]
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        print(
            f"FP={fp}, TN={tn}, "
            f"Accuracy={metrics['accuracy']:.4f}, FPR={fpr:.4f}"
        )

        metrics["fpr"] = fpr
        results.append(metrics)

    return results


def summarize(results):
    fps = [r["fp"] for r in results]
    tns = [r["tn"] for r in results]
    accs = [r["accuracy"] for r in results]
    fprs = [r["fpr"] for r in results]

    print("\n=== BASELINE FINAL SUMMARY ===")
    print(f"FP:       mean={np.mean(fps):.4f}, std={np.std(fps):.4f}")
    print(f"TN:       mean={np.mean(tns):.4f}, std={np.std(tns):.4f}")
    print(f"Accuracy: mean={np.mean(accs):.4f}, std={np.std(accs):.4f}")
    print(f"FPR:      mean={np.mean(fprs):.4f}, std={np.std(fprs):.4f}")


if __name__ == "__main__":
    results = evaluate_all_runs()
    summarize(results)
