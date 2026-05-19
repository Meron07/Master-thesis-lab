import os
from make_predicted_labels import make_predicted_labels
from make_true_labels import make_true_labels


def compute_metrics(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true) if y_true else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy
    }


if __name__ == "__main__":
    result_csv = os.path.expanduser(
        "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_replay_features.csv"
    )
    source_pcap_name = "exp1_7_noisy_replay.pcap"

    predicted_rows = make_predicted_labels(result_csv)
    y_pred = [row["predicted_label"] for row in predicted_rows]

    y_true = make_true_labels(result_csv, source_pcap_name)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)} y_pred={len(y_pred)}")

    metrics = compute_metrics(y_true, y_pred)

    print("Evaluation for one file")
    print(f"Total windows: {len(y_true)}")
    print(f"TP: {metrics['tp']}")
    print(f"FP: {metrics['fp']}")
    print(f"TN: {metrics['tn']}")
    print(f"FN: {metrics['fn']}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1-score: {metrics['f1']:.4f}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
