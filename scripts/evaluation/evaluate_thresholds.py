import csv
import os
import numpy as np


def load_predictions(csv_file, threshold):
    y_pred = []

    with open(csv_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            row = {k.strip(): v for k, v in row.items()}
            suspicious_count = int(row["suspicious_count"])
            pred = 1 if suspicious_count >= threshold else 0
            y_pred.append(pred)

    return y_pred


def compute_metrics(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    accuracy = (tp + tn) / len(y_true) if y_true else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "accuracy": accuracy,
    }


def evaluate_file(csv_file, threshold, true_label):
    y_pred = load_predictions(csv_file, threshold)
    y_true = [true_label] * len(y_pred)
    return compute_metrics(y_true, y_pred)


def summarize(metrics_list, keys):
    return {k: (np.mean([m[k] for m in metrics_list]), np.std([m[k] for m in metrics_list])) for k in keys}


def fmt(mean_std):
    return f"{mean_std[0]:.4f} ± {mean_std[1]:.4f}"


if __name__ == "__main__":
    thresholds = [3, 4, 5, 6, 7, 8]

    baseline_files = [
        os.path.expanduser(f"~/iec104-lab/results/exp1_6_windows_run_{i}_features.csv")
        for i in range(1, 11)
    ]

    replay_file = os.path.expanduser("~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_replay_features.csv")
    baseline_ref_file = os.path.expanduser("~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_baseline_features.csv")

    print("=== THRESHOLD SWEEP: IEC-104 NOISY CONDITION ===")

    rows = []

    for threshold in thresholds:
        baseline_metrics = [evaluate_file(f, threshold, 0) for f in baseline_files]
        replay_metrics = [evaluate_file(replay_file, threshold, 1)]

        base_summary = summarize(baseline_metrics, ["fp", "tn", "fpr", "accuracy"])
        rep_summary = summarize(replay_metrics, ["tp", "fn", "precision", "recall", "f1"])

        row = {
            "threshold": threshold,
            "baseline_fpr": base_summary["fpr"][0],
            "baseline_accuracy": base_summary["accuracy"][0],
            "replay_precision": rep_summary["precision"][0],
            "replay_recall": rep_summary["recall"][0],
            "replay_f1": rep_summary["f1"][0],
        }
        rows.append(row)

        print(f"\nThreshold {threshold}")
        print(f"  Baseline FPR:      {fmt(base_summary['fpr'])}")
        print(f"  Baseline Accuracy: {fmt(base_summary['accuracy'])}")
        print(f"  Replay Precision:  {fmt(rep_summary['precision'])}")
        print(f"  Replay Recall:     {fmt(rep_summary['recall'])}")
        print(f"  Replay F1:         {fmt(rep_summary['f1'])}")

    out_csv = os.path.expanduser("~/iec104-lab/results/iec104_threshold_sweep.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved threshold sweep to: {out_csv}")
