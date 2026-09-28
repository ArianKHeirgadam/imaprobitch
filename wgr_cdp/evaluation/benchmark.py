"""Small dependency-free benchmarking summaries."""


def benchmark_binary_predictions(actual, predicted):
    """Return confusion-matrix counts and standard binary metrics."""
    actual = list(actual)
    predicted = list(predicted)

    if len(actual) != len(predicted):
        raise ValueError("actual and predicted must have equal length")

    if any(value not in (0, 1, False, True) for value in actual + predicted):
        raise ValueError("binary values must be 0/1 or bool")

    tp = sum(bool(a) and bool(p) for a, p in zip(actual, predicted))
    tn = sum(not bool(a) and not bool(p) for a, p in zip(actual, predicted))
    fp = sum(not bool(a) and bool(p) for a, p in zip(actual, predicted))
    fn = sum(bool(a) and not bool(p) for a, p in zip(actual, predicted))

    total = len(actual)
    accuracy = (tp + tn) / total if total else 0.0

    precision_denominator = tp + fp
    recall_denominator = tp + fn
    specificity_denominator = tn + fp

    precision = tp / precision_denominator if precision_denominator else 0.0
    recall = tp / recall_denominator if recall_denominator else 0.0
    specificity = (
        tn / specificity_denominator
        if specificity_denominator
        else 0.0
    )

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
    }
