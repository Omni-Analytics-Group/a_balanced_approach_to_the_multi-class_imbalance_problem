#!/usr/bin/env python3
"""Independent, exact-rational tests of Mosley (2013) CBA.

Designed to be run from anywhere with Python 3.10+ and no dependencies:

    python formal-verification/scripts/verify_numeric.py

If src/cba.py is accessible in the enclosing GitHub repo, it additionally checks
that implementation against the exact reference results (float tolerance 1e-12).

This verifies finite examples computationally. It is NOT a replacement for the
universal proofs in Lean; the Lean build must be run separately.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import random
import sys
from fractions import Fraction
from pathlib import Path


def evaluate(matrix: tuple[tuple[int, ...], ...] | list[list[int]]) -> dict:
    k = len(matrix)
    assert k > 0 and all(len(row) == k for row in matrix)
    assert all(isinstance(x, int) and x >= 0 for row in matrix for x in row)
    rows = [sum(row) for row in matrix]
    cols = [sum(matrix[j][i] for j in range(k)) for i in range(k)]
    diagonal = [matrix[i][i] for i in range(k)]
    ratio = lambda n, d: Fraction(n, d) if d else Fraction(0)
    p = [ratio(diagonal[i], cols[i]) for i in range(k)]
    r = [ratio(diagonal[i], rows[i]) for i in range(k)]
    per_cba = [ratio(diagonal[i], max(rows[i], cols[i])) for i in range(k)]
    cba = sum(per_cba) / k
    macro_p = sum(p) / k
    macro_r = sum(r) / k
    accuracy = ratio(sum(diagonal), sum(rows))
    mean_min = sum(min(p[i], r[i]) for i in range(k)) / k
    gap = min(macro_p, macro_r) - cba
    gap_rhs = (sum(abs(p[i] - r[i]) for i in range(k)) / k - abs(macro_p - macro_r)) / 2
    same_direction = (all(p[i] <= r[i] for i in range(k)) or
                      all(r[i] <= p[i] for i in range(k)))
    mixed_strict = (any(p[i] < r[i] for i in range(k)) and
                    any(r[i] < p[i] for i in range(k)))

    assert cba == mean_min, (matrix, "Eq. 3.4/min equivalence")
    assert cba <= min(macro_p, macro_r), (matrix, "Theorem 3.2.1")
    assert Fraction(0) <= cba <= Fraction(1), (matrix, "0 <= CBA <= 1")
    assert gap == gap_rhs, (matrix, "exact gap identity")
    assert (gap == 0) == same_direction, (matrix, "iff equality condition")
    assert (gap > 0) == mixed_strict, (matrix, "iff strict condition")

    return {
        "k": k, "accuracy": accuracy, "cba": cba,
        "macro_precision": macro_p, "macro_recall": macro_r,
        "gap": gap, "gap_rhs": gap_rhs,
        "per_class_cba": per_cba, "p": p, "r": r,
    }


def render_exact(x):
    if isinstance(x, Fraction):
        return {"fraction": str(x), "decimal": round(float(x), 10)}
    if isinstance(x, list):
        return [render_exact(v) for v in x]
    if isinstance(x, dict):
        return {k: render_exact(v) for k, v in x.items()}
    return x


def load_repository_reference():
    # A ZIP's formal-verification/scripts/ -> formal-verification/ -> repo root.
    root = Path(__file__).resolve().parents[2]
    cba_path = root / "src" / "cba.py"
    if not cba_path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("original_repo_cba", cba_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(seed: int, random_cases: int, include_exhaustive_4: bool) -> dict:
    cases = {
        "figure_3_1_majority": [[2000, 0, 0], [600, 0, 0], [600, 0, 0]],
        "figure_3_1_partitioned": [[1000, 500, 500], [100, 500, 0], [100, 0, 500]],
        "two_class_strict_counterexample": [[1, 1], [0, 1]],
        "absent_class": [[10, 0, 0], [0, 5, 0], [0, 0, 0]],
        "all_zero": [[0, 0], [0, 0]],
        "perfect": [[4, 0, 0], [0, 5, 0], [0, 0, 7]],
        "one_class": [[7]],
        "one_class_empty": [[0]],
    }
    expected = {
        "figure_3_1_majority": (Fraction(5, 8), Fraction(5, 24)),
        "figure_3_1_partitioned": (Fraction(5, 8), Fraction(1, 2)),
        "two_class_strict_counterexample": (Fraction(2, 3), Fraction(1, 2)),
        "absent_class": (Fraction(1), Fraction(2, 3)),
        "all_zero": (Fraction(0), Fraction(0)),
        "perfect": (Fraction(1), Fraction(1)),
        "one_class": (Fraction(1), Fraction(1)),
        "one_class_empty": (Fraction(0), Fraction(0)),
    }
    reference = load_repository_reference()
    reference_checked = 0
    checks = 0

    def check(matrix):
        nonlocal checks, reference_checked
        result = evaluate(matrix)
        checks += 1
        if reference is not None:
            assert abs(reference.class_balance_accuracy(matrix) - float(result["cba"])) < 1e-12
            assert abs(reference.accuracy(matrix) - float(result["accuracy"])) < 1e-12
            assert abs(reference.macro_precision(matrix) - float(result["macro_precision"])) < 1e-12
            assert abs(reference.balanced_accuracy(matrix) - float(result["macro_recall"])) < 1e-12
            reference_checked += 1
        return result

    named = {name: check(matrix) for name, matrix in cases.items()}
    for name, (accuracy, cba) in expected.items():
        assert named[name]["accuracy"] == accuracy, name
        assert named[name]["cba"] == cba, name

    exhaustive = {}
    for k, limit in [(2, 6), (3, 2)] + ([(4, 2)] if include_exhaustive_4 else []):
        n = 0
        for entries in itertools.product(range(limit), repeat=k * k):
            matrix = tuple(tuple(entries[i * k + j] for j in range(k)) for i in range(k))
            check(matrix)
            n += 1
        exhaustive[f"{k}x{k}_entries_0_to_{limit-1}"] = n

    rng = random.Random(seed)
    for _ in range(random_cases):
        k = rng.randrange(1, 8)
        # Favor zeroes, severe skew, and a few very large counts.
        choices = (0, 0, 0, 1, 2, 3, 7, 100, 10000)
        matrix = [[rng.choice(choices) for _ in range(k)] for _ in range(k)]
        check(matrix)

    return {
        "status": "PASS",
        "type": "independent computational checks; not Lean kernel verification",
        "seed": seed,
        "named_examples": render_exact(named),
        "exhaustive_families": exhaustive,
        "random_cases": random_cases,
        "total_matrices_checked": checks,
        "repository_reference_found": reference is not None,
        "repository_reference_comparisons": reference_checked,
        "properties_checked_per_matrix": [
            "Equation 3.4 equals mean per-class min(P,R)",
            "Theorem 3.2.1 bound",
            "0 <= CBA <= 1",
            "exact gap identity",
            "equality iff all per-class comparisons are aligned",
            "strict gap iff both strict orientations occur",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2013)
    parser.add_argument("--random-cases", type=int, default=10_000)
    parser.add_argument("--quick", action="store_true", help="skip 65536 binary 4x4 matrices")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = run(args.seed, args.random_cases, not args.quick)
    content = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
    print("PASS: {total_matrices_checked:,} matrices; {repository_reference_comparisons:,} "
          "comparisons with repo src/cba.py".format(**report))
    for name in ["figure_3_1_majority", "figure_3_1_partitioned",
                 "two_class_strict_counterexample", "absent_class", "all_zero"]:
        r = report["named_examples"][name]
        print(f"  {name:32} accuracy={r['accuracy']['fraction']:>6}"
              f" CBA={r['cba']['fraction']:>6} gap={r['gap']['fraction']:>5}")
    if args.output:
        print(f"JSON: {args.output}")


if __name__ == "__main__":
    main()
