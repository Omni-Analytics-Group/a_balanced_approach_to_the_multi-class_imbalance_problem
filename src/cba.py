"""Reference implementation of Class Balance Accuracy (CBA).

CBA was introduced in L. Mosley, "A Balanced Approach to the Multi-class
Imbalance Problem", PhD thesis, Iowa State University, 2013 (Eq. 3.4):

    CBA = (1 / k) * sum_i  c_ii / max(c_i., c_.i)

where c_ii is the count on the diagonal of a k-by-k confusion matrix, c_i. is
the row total (actual members of class i) and c_.i is the column total
(observations predicted into class i). Per class it keeps the smaller of
recall and precision, so CBA is a lower bound on both macro recall
(balanced accuracy) and macro precision (Theorem 3.2.1).

Rows are actual classes and columns are predicted classes throughout.
No third-party dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence

Matrix = Sequence[Sequence[float]]


def _validated(matrix: Matrix) -> tuple[tuple[float, ...], ...]:
    """Return an immutable copy of a square, non-negative confusion matrix."""
    rows = tuple(tuple(row) for row in matrix)
    k = len(rows)
    if k == 0:
        raise ValueError("confusion matrix is empty")
    if any(len(row) != k for row in rows):
        raise ValueError("confusion matrix must be square (k rows by k columns)")
    # `not value >= 0` also rejects NaN, which compares false against everything.
    if any(not value >= 0 for row in rows for value in row):
        raise ValueError("confusion matrix counts must be non-negative numbers")
    return rows


def _row_totals(rows: tuple[tuple[float, ...], ...]) -> list[float]:
    return [sum(row) for row in rows]


def _column_totals(rows: tuple[tuple[float, ...], ...]) -> list[float]:
    return [sum(row[j] for row in rows) for j in range(len(rows))]


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def per_class_cba(matrix: Matrix) -> list[float]:
    """Per-class contributions c_ii / max(row total, column total) (Eq. 3.5a).

    A class that is never observed and never predicted contributes 0, so it
    lowers the average. Drop such classes from the matrix if that is not wanted.
    """
    rows = _validated(matrix)
    actual, predicted = _row_totals(rows), _column_totals(rows)
    return [_ratio(rows[i][i], max(actual[i], predicted[i])) for i in range(len(rows))]


def class_balance_accuracy(matrix: Matrix) -> float:
    """Class Balance Accuracy: the mean of the per-class contributions."""
    parts = per_class_cba(matrix)
    return sum(parts) / len(parts)


def accuracy(matrix: Matrix) -> float:
    """Overall accuracy: correct predictions over all observations."""
    rows = _validated(matrix)
    total = sum(_row_totals(rows))
    return _ratio(sum(rows[i][i] for i in range(len(rows))), total)


def per_class_recall(matrix: Matrix) -> list[float]:
    rows = _validated(matrix)
    actual = _row_totals(rows)
    return [_ratio(rows[i][i], actual[i]) for i in range(len(rows))]


def per_class_precision(matrix: Matrix) -> list[float]:
    rows = _validated(matrix)
    predicted = _column_totals(rows)
    return [_ratio(rows[i][i], predicted[i]) for i in range(len(rows))]


def balanced_accuracy(matrix: Matrix) -> float:
    """Balanced accuracy: macro-averaged recall. Not the same thing as CBA."""
    recalls = per_class_recall(matrix)
    return sum(recalls) / len(recalls)


def macro_precision(matrix: Matrix) -> float:
    precisions = per_class_precision(matrix)
    return sum(precisions) / len(precisions)


def macro_f1(matrix: Matrix) -> float:
    recalls, precisions = per_class_recall(matrix), per_class_precision(matrix)
    scores = [_ratio(2 * p * r, p + r) for p, r in zip(precisions, recalls)]
    return sum(scores) / len(scores)


def g_mean(matrix: Matrix) -> float:
    """Geometric mean of per-class recall. Zero if any class is never recalled."""
    recalls = per_class_recall(matrix)
    product = 1.0
    for recall in recalls:
        product *= recall
    return product ** (1.0 / len(recalls))


def confusion_matrix(actual: Sequence, predicted: Sequence, labels: Sequence | None = None) -> list[list[int]]:
    """Build a confusion matrix (rows actual, columns predicted) from label vectors."""
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same length")
    ordered = list(labels) if labels is not None else sorted(set(actual) | set(predicted))
    index = {label: position for position, label in enumerate(ordered)}
    counts = [[0] * len(ordered) for _ in ordered]
    for truth, guess in zip(actual, predicted):
        if truth not in index or guess not in index:
            raise ValueError(f"label not in labels: {truth!r} or {guess!r}")
        counts[index[truth]][index[guess]] += 1
    return counts


if __name__ == "__main__":
    # Figure 3.1 of the dissertation: two models with identical accuracy.
    examples = {
        "all-red model": [[2000, 0, 0], [600, 0, 0], [600, 0, 0]],
        "partitioned model": [[1000, 500, 500], [100, 500, 0], [100, 0, 500]],
    }
    for name, table in examples.items():
        print(
            f"{name:18s} accuracy={accuracy(table):.3f} "
            f"balanced accuracy={balanced_accuracy(table):.3f} "
            f"CBA={class_balance_accuracy(table):.3f}"
        )
