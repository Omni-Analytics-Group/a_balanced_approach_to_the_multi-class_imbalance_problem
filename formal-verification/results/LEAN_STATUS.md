# Formal verification status — November 22, 2026

**Status:** Verified for the selected formalized theorems in the supplied Lean project.
**Build environment:** Windows / PowerShell, Lean 4.36.0 toolchain as pinned in `lean-toolchain`, with pinned Mathlib `v4.36.0`.
**Evidence:** User-supplied terminal results of strict Lake builds and an axiom audit. The package compiler was not rerun in the document-authoring environment.

## Strict Lake builds

The following commands completed successfully with **`--wfail`** (warnings treated as failures):

```text
lake build --wfail MosleyCBA.Core
Build completed successfully (18251 jobs).

lake build --wfail MosleyCBA.Properties
Build completed successfully (18253 jobs).

lake build --wfail MosleyCBA.Examples
Build completed successfully (18255 jobs).

lake build --wfail
Build completed successfully (18258 jobs).
```

No compiler errors or warnings appeared in the successful v7 strict builds.

## Audited theorem dependencies

The output of `lake env lean MosleyCBA/AxiomAudit.lean` reports
**`[propext, Classical.choice, Quot.sound]`** for each of these nine theorems:

```text
MosleyCBA.originalFormula_eq_cbaOfMatrix
MosleyCBA.originalFormula_le_min_macro
MosleyCBA.cba_gap_identity
MosleyCBA.abs_macro_diff_le_mean_abs_diff
MosleyCBA.cba_eq_min_macro_iff
MosleyCBA.cba_lt_min_macro_iff
MosleyCBA.originalFormula_bounds
MosleyCBA.figure31_majority_cba
MosleyCBA.figure31_partitioned_cba
```

None of the nine audited theorem statements uses `sorryAx` or a custom project axiom. The three listed axioms are standard foundations of Lean's classical mathematics. The successful builds cover all module declarations, while this listed `#print axioms` report explicitly audits these nine selected theorems.

## Independent numerical validation

Separately, the bundled exact-arithmetic Python audit previously passed **77,352 matrices**: exhaustive families of small confusion matrices, 10,000 seeded random cases, and eight named cases. That initial run did **not** compare directly against the original repository's `src/cba.py` (`repository_reference_comparisons` was zero). The Python cross-implementation test should be rerun within a clone containing `src/cba.py`; do not claim it passed until the JSON reports a nonzero number of comparisons.

## Publication considerations

- This verifies the **encoded mathematical properties** of CBA, not the dissertation's empirical experiments, predictive performance, or the scientific originality of derived identities.
- The gap identity, equality and strictness criteria are companion extensions, **not** attributed to Mosley (2013) as original dissertation results.
- A successful public GitHub Actions workflow and immutable commit ID remain recommended for third-party reproducibility; this locally observed success does not imply CI has already been run.
- Preserve exact source revisions and toolchain versions with the eventual public release.
