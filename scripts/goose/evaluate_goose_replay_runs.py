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

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall,
        "f1": f1, "accuracy": accuracy
    }

def evaluate_all_runs():
    results = []

    for i in range(1, 11):
        print(f"\nEvaluating GOOSE replay run_{i}...")

        csv_file = os.path.expanduser(
            f"~/iec104-lab/multi_runs/goose/features/replay/run_{i}_features.csv"
        )

        df = pd.read_csv(csv_file)
        y_pred = df["replay_alert"].astype(int).tolist()
        y_true = [1] * len(y_pred)

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

    print("\n=== GOOSE REPLAY FINAL SUMMARY ===")
    print(f"TP:        mean={np.mean(tps):.4f}, std={np.std(tps):.4f}")
    print(f"FN:        mean={np.mean(fns):.4f}, std={np.std(fns):.4f}")
    print(f"Precision: mean={np.mean(precisions):.4f}, std={np.std(precisions):.4f}")
    print(f"Recall:    mean={np.mean(recalls):.4f}, std={np.std(recalls):.4f}")
    print(f"F1-score:  mean={np.mean(f1s):.4f}, std={np.std(f1s):.4f}")

if __name__ == "__main__":
    results = evaluate_all_runs()
    summarize(results)
