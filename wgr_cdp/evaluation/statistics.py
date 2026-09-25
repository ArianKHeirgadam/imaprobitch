"""Statistical evaluation utilities."""

from collections import Counter


def frequency_analysis(values):
    if not values:
        return {}

    counts = Counter(values)
    total = len(values)

    return {
        key: count / total
        for key, count in counts.items()
    }
