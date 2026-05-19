import os
import numpy as np
import pandas as pd

def compute_metrics(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(y_true) if y_true else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall,
        "f1": f1, "accuracy": accuracy, "fpr": fpr
    }

def evaluate_all_runs():
    results = []

    for i in range(1, 11):
        print(f"\nEvaluating GOOSE baseline run_{i}...")

        csv_file = os.path.expanduser(
            f"~/iec104-lab/multi_runs/goose/features/baseline/run_{i}_features.csv"
        )

        df = pd.read_csv(csv_file)
        y_pred = df["replay_alert"].astype(int).tolist()
        y_true = [0] * len(y_pred)

        metrics = compute_metrics(y_true, y_pred)
        print(
            f"FP={metrics['fp']}, TN={metrics['tn']}, "
            f"Accuracy={metrics['accuracy']:.4f}, FPR={metrics['fpr']:.4f}"
        )
        results.append(metrics)

    return results

def summarize(results):
    fps = [r["fp"] for r in results]
    tns = [r["tn"] for r in results]
    accs = [r["accuracy"] for r in results]
    fprs = [r["fpr"] for r in results]

    print("\n=== GOOSE BASELINE FINAL SUMMARY ===")
    print(f"FP:       mean={np.mean(fps):.4f}, std={np.std(fps):.4f}")
    print(f"TN:       mean={np.mean(tns):.4f}, std={np.std(tns):.4f}")
    print(f"Accuracy: mean={np.mean(accs):.4f}, std={np.std(accs):.4f}")
    print(f"FPR:      mean={np.mean(fprs):.4f}, std={np.std(fprs):.4f}")

if __name__ == "__main__":
    results = evaluate_all_runs()
    summarize(results)
