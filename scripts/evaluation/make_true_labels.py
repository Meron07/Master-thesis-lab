import os
from get_ground_truth import get_numeric_label
from make_predicted_labels import make_predicted_labels


def make_true_labels(result_csv, source_pcap_name):
    predicted_rows = make_predicted_labels(result_csv)
    true_value = get_numeric_label(source_pcap_name)

    if true_value not in (0, 1):
        raise ValueError(f"Unsupported ground truth label for this step: {source_pcap_name} -> {true_value}")

    true_labels = [true_value] * len(predicted_rows)
    return true_labels


if __name__ == "__main__":
    result_csv = os.path.expanduser(
        "~/iec104-lab/results/exp1_6_windows_exp1_7_noisy_replay_features.csv"
    )

    source_pcap_name = "exp1_7_noisy_replay.pcap"

    true_labels = make_true_labels(result_csv, source_pcap_name)

    print(f"Total true labels: {len(true_labels)}")
    print("First 10 true labels:")
    print(true_labels[:10])
    print(f"Unique true label values: {sorted(set(true_labels))}")
