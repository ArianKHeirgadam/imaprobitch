"""Multiple-testing correction utilities."""


def benjamini_hochberg(p_values):
    """Return Benjamini-Hochberg adjusted p-values in input order."""
    values = [float(value) for value in p_values]

    if any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("p-values must be between 0 and 1")

    n = len(values)
    if n == 0:
        return []

    ranked = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    adjusted = [1.0] * n
    running = 1.0

    for rank in range(n, 0, -1):
        index, p_value = ranked[rank - 1]
        corrected = min(1.0, p_value * n / rank)
        running = min(running, corrected)
        adjusted[index] = running

    return adjusted


def add_fdr(results, p_key="p_value", output_key="q_value"):
    """Copy result rows and attach BH-adjusted q-values."""
    rows = [dict(row) for row in results]
    p_values = [row.get(p_key, 1.0) for row in rows]
    q_values = benjamini_hochberg(p_values)

    for row, q_value in zip(rows, q_values):
        row[output_key] = q_value

    return rows


def filter_significant(results, alpha=0.05, p_key="q_value"):
    """Return rows whose selected p/q-value is <= alpha."""
    if not 0.0 < float(alpha) <= 1.0:
        raise ValueError("alpha must be in (0, 1]")

    return [
        dict(row)
        for row in results
        if float(row.get(p_key, 1.0)) <= float(alpha)
    ]
