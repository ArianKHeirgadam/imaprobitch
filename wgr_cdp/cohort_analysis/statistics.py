"""Small dependency-free statistics helpers for cohort comparison."""

from math import comb


def fisher_exact_2x2(a, b, c, d):
    """Return the two-sided Fisher exact p-value for a 2x2 table.

    Table layout:

        case    control
    yes   a       b
    no    c       d

    The implementation is dependency-free and intended for small genomic
    cohort analyses where exact testing is useful.
    """
    values = [int(a), int(b), int(c), int(d)]
    if any(value < 0 for value in values):
        raise ValueError("2x2 counts must be non-negative")

    row1 = a + b
    row2 = c + d
    col1 = a + c
    total = row1 + row2

    if total == 0:
        return 1.0

    def probability(x):
        if x < 0 or x > row1 or col1 - x < 0 or col1 - x > row2:
            return 0.0
        return (
            comb(row1, x)
            * comb(row2, col1 - x)
            / comb(total, col1)
        )

    observed = probability(a)

    lower = max(0, col1 - row2)
    upper = min(row1, col1)

    p_value = 0.0
    for x in range(lower, upper + 1):
        p = probability(x)
        if p <= observed + 1e-15:
            p_value += p

    return min(1.0, max(0.0, p_value))
