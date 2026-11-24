# CBA formal verification: Lean 4 + Mathlib

**Companion to:** Lawrence Mosley, *A Balanced Approach to the Multi-Class Imbalance Problem* (Iowa State University, 2013), [DOI:10.31274/etd-180810-3375](https://doi.org/10.31274/etd-180810-3375).

This project separates the dissertation's **original mathematical claim** from additional results we can derive from its definition. The goal is to produce an independent, reproducible machine-checked record of the mathematics behind Class Balance Accuracy (CBA).

> [!IMPORTANT]
> **Verification status (November 22, 2026): VERIFIED.** The user executed Lean 4.36.0 / Mathlib builds in Windows PowerShell: `lake build --wfail` passed for Core, Properties, Examples and the full library (**18,258 jobs**), with zero warnings. An axiom audit of nine central theorems reports only Lean's standard `propext`, `Classical.choice` and `Quot.sound`—no `sorryAx`. The accompanying exact-rational Python test separately passed 77,352 matrices. See [verification record](results/LEAN_STATUS.md). A public CI success URL is not yet documented.

## Folder structure

```text
formal-verification/
├── README.md                 # Build/verification instructions (this file)
├── THEORY.md                 # In-depth mathematical companion
├── lean-toolchain            # Lean 4.36.0
├── lakefile.toml             # Pinned Mathlib v4.36.0
├── MosleyCBA.lean            # Root import; lake build compiles all modules
├── MosleyCBA/
│   ├── Core.lean             # Confusion matrices, Eq. 3.4, Theorem 3.2.1
│   ├── Properties.lean       # Gap, equality iff, strictness, bounds
│   ├── Examples.lean         # Exact Fig. 3.1 and edge-case Lean theorems
│   └── AxiomAudit.lean       # Print which Lean axioms the theorems use
├── scripts/
│   └── verify_numeric.py    # Independent exact Fraction tests
└── results/
    ├── numeric_checks.json  # Result of local Python computation
    └── LEAN_STATUS.md        # Compilation status/what to report
```

The parent repository also receives `README_SECTION.md` (the stylized insertion for its main README), `formal-verification/scripts/insert_readme_section.py`, and an optional `.github/workflows/cba-lean.yml` workflow.

## 1. Install and build Lean

The project is pinned to Lean **v4.36.0** and the matching Mathlib release. Installation instructions: [Lean manual](https://lean-lang.org/lean4/doc/quickstart.html). On **Windows**, use VS Code with the Lean 4 extension or a PowerShell terminal with `elan`/`lake` installed. WSL/Ubuntu is also suitable.

From the **original GitHub repository root**:

```powershell
cd formal-verification
lake update
lake exe cache get
lake build --wfail
```

The first `lake update` and `lake exe cache get` require internet access. Downloaded Mathlib caches save substantial compilation time. Subsequent `lake build` runs should be much faster.

**A successful build has been reported**: Lean checks the proof terms against the kernel. Python numerical tests cannot replace this step. The sources intentionally contain no `sorry`, `admit`, or newly declared proof axioms; the build must confirm the code elaborates and type-checks as intended.

When changing proofs, rerun each stage and save its output. A future failed build means the modified formalization is not yet verified, even if the last published release passed.

```powershell
# From formal-verification/ in PowerShell
lake build --wfail MosleyCBA.Core       2>&1 | Tee-Object -FilePath core.log
lake build --wfail MosleyCBA.Properties 2>&1 | Tee-Object -FilePath properties.log
lake build --wfail MosleyCBA.Examples   2>&1 | Tee-Object -FilePath examples.log
lake build --wfail               2>&1 | Tee-Object -FilePath full-build.log
lake env lean MosleyCBA/AxiomAudit.lean 2>&1 | Tee-Object -FilePath axiom-audit.log
```

After each command, `$LASTEXITCODE` should be `0`. If not, provide the **complete first compiler error** and a few lines above it. Axiom audit output can be attached to the write-up after successful compilation. Mathlib may legitimately use Lean's standard axioms, such as `propext` or `Classical.choice`; `sorryAx` or introduced custom axioms would be unacceptable.

On Unix shells, the same commands work without `Tee-Object` (or use `2>&1 | tee core.log`, etc.).

## 2. Independent numeric tests

From the **original GitHub repository root**:

```bash
python formal-verification/scripts/verify_numeric.py \
  --random-cases 10000 \
  --output formal-verification/results/numeric_checks.json
```

The script works with **no third-party dependencies** and exact `fractions.Fraction` arithmetic. It tests:

1. Equation 3.4 equals the average of the minima of per-class precision/recall.
2. Theorem 3.2.1: CBA is no greater than either macro average.
3. `0 <= CBA <= 1`, including zero denominators.
4. The exact formula for the gap to the smaller macro average.
5. Equality if and only if all per-class precision/recall comparisons point the same way.
6. Strict inequality if and only if both opposite strict comparisons occur.

Test families: all 6^4 two-class matrices with entries 0–5; all 2^9 three-class binary matrices; all 2^16 four-class binary matrices; 10,000 seeded random matrices with 1–7 classes; and eight named edge cases. That is **77,352 matrices** in the default configuration.

**Cross-check with the original Python implementation:** Running this in the original repository automatically detects `src/cba.py` and also compares accuracy, CBA, macro precision, and balanced accuracy against that implementation. Our initial independent run, which did not have a local copy of the GitHub repository, had `repository_reference_comparisons: 0`. Please rerun inside the cloned repository to obtain those cross-implementation comparisons. It should report `repository_reference_comparisons: 77352` when all tests pass.

## 3. What's in the proof modules?

| Objective | File | Main theorem(s) | State |
|---|---|---|---|
| 1. Formal definition with zero denominators | `Core.lean` | `originalFormula_eq_cbaOfMatrix`, `ratio_max_eq_min_div` | Lean compiled; `--wfail` passed |
| 2. Original lower-bound theorem | `Core.lean` | `cba_le_min_macro`, `originalFormula_le_min_macro` | Lean compiled; `--wfail` passed |
| 3a. Exact gap identity | `Properties.lean` | `cba_gap_identity` | Lean compiled; `--wfail` passed |
| 3b. Equality and strictness iff | `Properties.lean` | `cba_eq_min_macro_iff`, `cba_lt_min_macro_iff` | Lean compiled; `--wfail` passed |
| 3c. Bounds | `Properties.lean` | `originalFormula_bounds` | Lean compiled; `--wfail` passed |
| 4. Figure 3.1 and edge cases | `Examples.lean` | `figure31_majority_cba`, `figure31_partitioned_cba`, etc. | Python and Lean checks passed |

See [THEORY.md](THEORY.md) for proofs, interpretation, caveats, and the precise mathematical claim behind each module.

## 4. Recorded verification and how to repeat it

The supplied user build record shows strict warning-free compilation and the nine-theorem axiom audit. See [`results/LEAN_STATUS.md`](results/LEAN_STATUS.md) for exact reported job counts, names, and qualifications.

For any new commit, run the bundled script from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_warning_free.ps1
```

Or invoke the commands manually:

```powershell
lake build --wfail MosleyCBA.Core
lake build --wfail MosleyCBA.Properties
lake build --wfail MosleyCBA.Examples
lake build --wfail
lake env lean MosleyCBA/AxiomAudit.lean
```

A successful build establishes successful elaboration and checking of its declarations. `#print axioms` identifies assumptions of the **nine selected results**; if new theorems are added, add them to `AxiomAudit.lean` and record the updated output. On GitHub, the workflow should run strict compilation and reject any `sorryAx` in this audit. Preserve the commit SHA and CI URL for future reproducibility.

**Cross-language parity pending:** The original independent Python run did not load `src/cba.py`. Rerun `verify_numeric.py` from the original repository root and retain its updated JSON before claiming reference-implementation parity.

## 5. Limits of the claim

- We establish mathematical properties **of CBA's definition**. This does not prove CBA is statistically superior to other metrics, unbiased for a population estimand, robust to data leakage, or the best optimization target for a classifier.
- Precision and recall are **real-valued functions** in abstract lemmas; the confusion-matrix instances use **natural-number counts**. This is intentional: it proves the inequality at maximum generality, while restricting the `[0,1]` statement to valid confusion matrices.
- Classes with neither real nor predicted observations contribute 0 under the repository's convention and still count as a class. If you remove such classes, you obtain a different index type and potentially a different CBA value.
- The **exact gap identity and equality characterization** are mathematical extensions offered by this project. They are not attributed as original statements of Mosley's dissertation.

## Sources

- L. Mosley (2013), [dissertation DOI](https://doi.org/10.31274/etd-180810-3375).
- [Original repository README](https://github.com/Omni-Analytics-Group/a_balanced_approach_to_the_multi-class_imbalance_problem).
- [Reference implementation](https://github.com/Omni-Analytics-Group/a_balanced_approach_to_the_multi-class_imbalance_problem/blob/main/src/cba.py).
- [Lean](https://lean-lang.org/) and [Mathlib documentation](https://leanprover-community.github.io/mathlib4_docs/).
