"""Tests for the Class Balance Accuracy reference implementation.

The fixtures are the worked examples from the dissertation (Figure 3.1 and
Table 3.3), so the code is checked against the published numbers.
"""

import itertools
import random

import pytest

from src.cba import (
    accuracy,
    balanced_accuracy,
    class_balance_accuracy,
    macro_precision,
    per_class_cba,
)

# Figure 3.1: 2000 red, 600 blue, 600 green. Rows are actual, columns predicted.
# Class order: red, blue, green.
ALL_RED = [[2000, 0, 0], [600, 0, 0], [600, 0, 0]]
PARTITIONED = [[1000, 500, 500], [100, 500, 0], [100, 0, 500]]


def test_figure_3_1_models_share_accuracy():
    assert accuracy(ALL_RED) == pytest.approx(0.625)
    assert accuracy(PARTITIONED) == pytest.approx(0.625)


def test_figure_3_1_cba_separates_the_models():
    assert class_balance_accuracy(ALL_RED) == pytest.approx(0.208, abs=5e-4)
    assert class_balance_accuracy(PARTITIONED) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "matrix, expected",
    [
        ([[40, 20], [10, 0]], 0.333),
        ([[41, 19], [10, 0]], 0.341),
        ([[40, 20], [9, 1]], 0.357),
    ],
)
def test_table_3_3_two_class_examples(matrix, expected):
    assert class_balance_accuracy(matrix) == pytest.approx(expected, abs=1e-3)


def test_perfect_classifier_scores_one():
    assert class_balance_accuracy([[5, 0, 0], [0, 7, 0], [0, 0, 90]]) == 1.0


def test_per_class_values_average_to_cba():
    parts = per_class_cba(PARTITIONED)
    assert parts == pytest.approx([0.5, 0.5, 0.5])
    assert sum(parts) / len(parts) == pytest.approx(class_balance_accuracy(PARTITIONED))


def test_theorem_3_2_1_lower_bound_on_random_matrices():
    rng = random.Random(2013)
    for _ in range(2000):
        k = rng.randint(2, 6)
        matrix = [[rng.randint(0, 50) for _ in range(k)] for _ in range(k)]
        if any(sum(row) == 0 for row in matrix):
            continue
        if any(sum(matrix[i][j] for i in range(k)) == 0 for j in range(k)):
            continue
        cba = class_balance_accuracy(matrix)
        assert cba <= balanced_accuracy(matrix) + 1e-12
        assert cba <= macro_precision(matrix) + 1e-12
        assert 0.0 <= cba <= 1.0


def test_class_never_predicted_and_never_observed_contributes_zero():
    assert per_class_cba([[3, 0], [0, 0]]) == [1.0, 0.0]


@pytest.mark.parametrize(
    "bad",
    [[], [[1, 2], [3]], [[1, -1], [0, 2]], [[1, 2, 3], [4, 5, 6]], [[float("nan"), 1], [1, 1]]],
)
def test_invalid_matrices_are_rejected(bad):
    with pytest.raises(ValueError):
        class_balance_accuracy(bad)


def test_input_is_not_mutated():
    matrix = [[1, 2], [3, 4]]
    snapshot = [row[:] for row in matrix]
    class_balance_accuracy(matrix)
    assert matrix == snapshot


def test_cba_is_invariant_to_class_relabeling():
    for perm in itertools.permutations(range(3)):
        shuffled = [[PARTITIONED[i][j] for j in perm] for i in perm]
        assert class_balance_accuracy(shuffled) == pytest.approx(0.5)


def test_confusion_matrix_from_labels_round_trips():
    from src.cba import confusion_matrix

    actual = ["a", "a", "b", "c", "c", "c"]
    predicted = ["a", "b", "b", "c", "c", "a"]
    assert confusion_matrix(actual, predicted) == [[1, 1, 0], [0, 1, 0], [1, 0, 2]]
    with pytest.raises(ValueError):
        confusion_matrix(["a"], ["a", "b"])
    with pytest.raises(ValueError):
        confusion_matrix(["a"], ["z"], labels=["a"])


def test_g_mean_and_macro_f1_on_figure_3_1():
    from src.cba import g_mean, macro_f1

    assert g_mean(ALL_RED) == 0.0
    # Every class has recall and precision of 0.5 and 5/6 in some order, so F1 = 0.625.
    assert macro_f1(PARTITIONED) == pytest.approx(0.625)
