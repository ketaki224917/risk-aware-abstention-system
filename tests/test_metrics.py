from raa.eval.metrics import binary_classification_metrics, selective_metrics


def test_binary_and_selective_metrics_use_malignant_as_class_zero():
    targets = [0, 0, 1, 1]
    predictions = [1, 0, 0, 1]
    baseline = binary_classification_metrics(targets, predictions)
    assert baseline["false_negatives"] == 1
    assert baseline["false_positives"] == 1
    selective = selective_metrics(
        targets, predictions, ["Human Review", "Automatic", "Assisted", "Automatic"]
    )
    assert selective["automatic_count"] == 2
    assert selective["false_negatives_routed_away"] == 1
    assert selective["review_workload_count"] == 2
