# The mathematics of Class Balance Accuracy, formalized in Lean

**A detailed theoretical companion to *A Balanced Approach to the Multi-Class Imbalance Problem* (Mosley, 2013)**

**Verified companion version:** 22 November 2026  
**Proof system:** Lean 4 + Mathlib (pinned to 4.36.0)  
**Kernel status:** **VERIFIED FOR THE LISTED RESULTS.** User-supplied Windows/Lean 4.36.0 runs passed all modules using `lake build --wfail`, and the nine-theorem axiom audit reported only `propext`, `Classical.choice`, and `Quot.sound` (no `sorryAx`). See [`results/LEAN_STATUS.md`](results/LEAN_STATUS.md).  
**Computational status:** independent exact-rational testing PASSED on 77,352 confusion matrices.

---

## Abstract

Class Balance Accuracy (CBA) assesses a multi-class classifier by averaging, across classes, the smaller of that class's precision and recall. Its central mathematical property is that CBA never exceeds either macro-averaged precision or macro-averaged recall. The distinction between *averaging per-class minima* and *taking the minimum of two macro averages* matters: they are not generally equal. This companion gives precise mathematical statements, elementary proofs, compiled Lean 4 formalizations, an exact gap decomposition, a complete condition for equality, bounds in the unit interval, handling of empty classes, and reproducible numerical examples adapted from Figure 3.1. The new gap and equality results are derived here rather than attributed to the dissertation.

## 1. Source and research objective

Lawrence S. D. Mosley's 2013 Iowa State University dissertation introduced CBA to address multi-class imbalance where overall accuracy can hide severe failures on individual classes. The reference implementation in the companion [GitHub repository](https://github.com/Omni-Analytics-Group/a_balanced_approach_to_the_multi-class_imbalance_problem/blob/main/src/cba.py) describes the exact formula as Equation 3.4 and its simultaneous lower-bound property as Theorem 3.2.1. This project concentrates on those mathematical aspects of Chapter 3, **not** on formalizing its model-selection experiments or claiming that Lean proves empirical model superiority. **Source limitation:** the university-hosted dissertation PDF was not retrievable in the authoring environment; the equation/theorem numbering and Figure 3.1 matrices were therefore checked against the public repository and its `src/cba.py` reference implementation rather than re-extracted directly from the PDF.

Our objectives are:

1. Express the original formula with a finite nonempty class index and a nonnegative confusion matrix; prove its per-class-minimum equivalence, including empty rows and columns.
2. Check the lower-bound inequality of Theorem 3.2.1.
3. Derive new statements: a quantitative gap identity, necessary and sufficient equality conditions, strictness, and the range `[0,1]` for valid confusion matrices.
4. Check Figure 3.1 and edge cases with exact rational arithmetic as well as Lean-checked theorem statements.

We separate three types of evidence: **ordinary mathematical proof** on these pages, **finite computational checking** in Python, and **machine-checked universal proof** in Lean. All three are now supported: the mathematical arguments below, the independent finite Python audit, and successful user-reported strict Lean builds with an explicit nine-theorem axiom audit. Only the stated mathematical definitions and results are being verified; no claim is made about the dissertation’s empirical hypotheses.

## 2. Definitions and assumptions

### 2.1 Confusion matrix

Let $I$ be a finite nonempty set of classes, with $k=\lvert I\rvert \ge1$, and let
$C=(c_{ij})_{i,j\in I}$ be a matrix of **nonnegative integer** counts:

- $c_{ij}$: instances whose true label is $i$ and predicted label is $j$.
- $d_i=c_{ii}$: correct predictions for class $i$.
- $a_i=\sum_j c_{ij}$: actual support, or row total.
- $b_i=\sum_j c_{ji}$: predicted support, or column total.

Because all counts are nonnegative, $0\le d_i\le a_i$ and $0\le d_i\le b_i$. No assumption is made that every class occurs or is predicted.

Define per-class precision and recall by

$$
P_i=\begin{cases}d_i/b_i&b_i>0,\\0&b_i=0,\end{cases}
\qquad
R_i=\begin{cases}d_i/a_i&a_i>0,\\0&a_i=0.\end{cases}
$$

This is the repository's convention: when a class has no predictions, its precision is 0; when it has no actual members, its recall is 0. Since $d_i\le a_i,b_i$, either zero denominator implies $d_i=0$. In Lean's real-number field, `0 / 0 = 0`; thus the definitions can be written directly using division. This **totalized division convention is important**: ordinary analysis often treats 0/0 as undefined.

The macro averages are

$$
\overline P=\frac1k\sum_i P_i,\qquad
\overline R=\frac1k\sum_i R_i.
$$

The original CBA formula, Equation 3.4, is

$$
\boxed{\mathrm{CBA}(C)=\frac1k\sum_i\frac{d_i}{\max(a_i,b_i)}}.
$$

*Equation (1) — Original CBA formula (dissertation Equation 3.4).*

An absent class — one with $a_i=b_i=0$ — contributes zero and **still occupies one of the $k$ slots**. Do not silently remove such classes during formal verification or comparisons with external libraries.

### 2.2 What does “arbitrary number of classes” mean?

The Lean theory is parameterized by a type `ι` satisfying `[Fintype ι] [Nonempty ι]`. That means *any finite positive number* of labels, rather than a hardcoded binary or three-class case. In the executable examples, we instantiate it with `Fin 2` and `Fin 3`. The latter are concrete examples of the general theorem, not its only scope.

A zero-class type is deliberately excluded: the statistic requires division by the number of classes. An empty dataset **with one or more declared classes** is permitted; all counts can be zero.

## 3. Objective 1: equivalence of the two CBA definitions

### Proposition 1: termwise equivalence

For every class,

$$
\frac{d_i}{\max(a_i,b_i)}
=\min\left(\frac{d_i}{a_i},\frac{d_i}{b_i}\right)
=\min(R_i,P_i).
$$

*Equation (2) — Termwise equivalence.*

**Proof.** Suppose first that $a_i\le b_i$. Then $\max(a_i,b_i)=b_i$. When $a_i>0$, division of a nonnegative numerator by a larger positive denominator gives a smaller quotient, so $d_i/b_i\le d_i/a_i$. When $a_i=0$, the diagonal is zero as well, and both ratios are zero under the stated convention. The case $b_i\le a_i$ follows symmetrically. ◻

Average (2) over classes:

$$
\boxed{\mathrm{CBA}=\frac1k\sum_i\min(P_i,R_i)}.
$$

*Equation (3) — CBA as the mean of per-class minima.*

The Lean file `MosleyCBA/Core.lean` gives `ratio_max_eq_min_div`, `originalTerm_eq_min`, and `originalFormula_eq_cbaOfMatrix` as Lean-checked proofs. The intermediate diagonal inequalities guarantee that the proof remains valid when a denominator is zero.

**Why the equivalence matters:** Equation (1) is easiest to compute from a confusion matrix; Equation (3) makes the conceptual behavior of the measure immediately apparent.

## 4. Objective 2: Theorem 3.2.1, the lower-bound property

### Theorem 1 (Mosley 2013, Theorem 3.2.1)

For every finite nonempty class set,

$$
\boxed{\mathrm{CBA}\le\overline P
\quad\text{and}\quad
\mathrm{CBA}\le\overline R.}
$$

*Equation (4) — Simultaneous macro-average bounds.*

Equivalently,

$$
\boxed{\mathrm{CBA}\le\min(\overline P,\overline R)}.
$$

*Equation (5) — Bound by the smaller macro average.*

**Proof.** For every $i$,

$$
\min(P_i,R_i)\le P_i,
\qquad \min(P_i,R_i)\le R_i.
$$

Summing each inequality and dividing by $k>0$ gives (4). ◻

This argument requires **no** independence, distributional assumptions, class-size constraints, or even that the vectors came from a confusion matrix. It works for any real-valued functions $P,R:I\to\mathbb{R}$. The confusion-matrix version is obtained by substituting the definitions of precision and recall.

**Interpretation:** A CBA of 0.80 implies that both the macro precision and macro recall are at least 0.80. The converse is generally false. Importantly, the theorem says **“lower than each average”**, not **“equal to the smaller average.”**

Lean theorem names: `cba_le_min_macro` (abstract), `cbaOfMatrix_le_min_macro`, and `originalFormula_le_min_macro` (original Equation 3.4).

## 5. Objective 3: stronger theory

### 5.1 Exact gap identity: the dispersion penalty

Define the **CBA deficit** relative to the smaller macro average by

$$
D=\min(\overline P,\overline R)-\mathrm{CBA}.
$$

The dissertation's theorem guarantees $D\ge0$. We can say *exactly* how much lower CBA is.

### Theorem 2 (derived extension)

$$
\boxed{
D=\frac12\left[
\frac1k\sum_i\lvert P_i-R_i\rvert -
\lvert \overline P-\overline R\rvert 
\right].}
$$

*Equation (6) — Exact CBA gap identity.*

**Proof.** For any real numbers $x,y$,

$$
\min(x,y)=\frac{x+y-\lvert x-y\rvert }{2}.
$$

Apply this identity to each $(P_i,R_i)$ inside the CBA sum:

$$
\mathrm{CBA}=\frac{\overline P+\overline R}{2}-
\frac1{2k}\sum_i\lvert P_i-R_i\rvert .
$$

Apply the same identity to $(\overline P,\overline R)$:

$$
\min(\overline P,\overline R)
=\frac{\overline P+\overline R}{2}-
\frac12\lvert \overline P-\overline R\rvert .
$$

Subtract to obtain (6). ◻

The finite-sum triangle inequality gives

$$
\left\lvert\frac1k\sum_i(P_i-R_i)\right\rvert
\le\frac1k\sum_i\lvert P_i-R_i\rvert .
$$

Consequently, the right-hand side of (6) is always nonnegative — an independent explanation of the original lower-bound result.

**Practical interpretation:** the first term measures the average classwise disagreement between precision and recall. The second measures only the *net* disagreement after averaging signed differences. When different classes' imbalances cancel out in the macro averages, CBA still preserves the penalty for the individual trade-offs.

For additional intuition, let

$$
A=\sum_i\max(P_i-R_i,0),\qquad
B=\sum_i\max(R_i-P_i,0).
$$

Then $\sum_i\lvert P_i-R_i\rvert =A+B$, $\sum_i(P_i-R_i)=A-B$, so the deficit is also

$$
\boxed{D=\frac{\min(A,B)}{k}}.
$$

*Equation (7) — Equivalent formula for the gap.*

Equation (7) shows that the deficit is the smaller total of the two *opposing* precision/recall tendencies. It is a useful alternative interpretation derived by ordinary algebra; this particular rearrangement is **not yet a separate Lean theorem in the accompanying verification release**.

Lean: `min_eq_half_sub_abs`, `cba_gap_identity`, and `abs_macro_diff_le_mean_abs_diff` in `Properties.lean`.

### 5.2 Exact equality and strictness conditions

**Theorem 3 (derived extension).** The inequality in (5) becomes equality **if and only if** all classes have the same weak precision/recall orientation:

$$
\boxed{
\mathrm{CBA}=\min(\overline P,\overline R)
\iff
\bigl(\forall i:\ P_i\le R_i\bigr)
\ \lor\
\bigl(\forall i:\ R_i\le P_i\bigr).
}
$$

*Equation (8) — Equality characterization.*

The two conditions overlap whenever all $P_i=R_i$; equality within some classes is fine.

**Proof.** If $P_i\le R_i$ in every class, then every minimum is $P_i$, so $\mathrm{CBA}=\overline P$. Since the original theorem also shows $\mathrm{CBA}\le\overline R$, this is the smaller macro average. The case $R_i\le P_i$ is symmetric.

Conversely, the smaller macro average equals either $\overline P$ or $\overline R$. Suppose $\mathrm{CBA}=\overline P$. Then

$$
\sum_i\big(P_i-\min(P_i,R_i)\big)=0.
$$

Every summand is nonnegative. A finite sum of nonnegative reals can be zero only when *every* summand is zero. Thus $P_i=\min(P_i,R_i)$, hence $P_i\le R_i$ for every class. The alternative $\mathrm{CBA}=\overline R$ gives the other orientation. ◻

**Corollary (strictness).** CBA is *strictly* below both the minimum macro average in (5) precisely when there are classes $i,j$ such that

$$
P_i<R_i\quad\text{and}\quad R_j<P_j.
$$

Thus one class needs to have the stricter recall constraint while another has the stricter precision constraint. The definition does **not** imply that CBA is strictly below **both individual** macro averages in all cases — only when both opposite strict inequalities appear.

Lean: `macroPrecision_eq_cba_iff`, `macroRecall_eq_cba_iff`, `cba_eq_min_macro_iff`, `cba_lt_min_macro_iff` in `Properties.lean`.

### 5.3 Bounds and boundary cases

**Theorem 4 (derived extension).** For any natural-number confusion matrix with $k\ge1$,

$$
\boxed{0\le\mathrm{CBA}\le1}.
$$

*Equation (9) — Bounds of the CBA statistic.*

**Proof.** Every per-class precision and recall is in $[0,1]$ because $0\le d_i\le a_i,b_i$ and zero denominators are defined to give zero. Their minimum is also in $[0,1]$. The mean of $k$ such numbers lies in $[0,1]$. ◻

Lean: `precisionOf_bounds`, `recallOf_bounds`, `cbaOfMatrix_bounds`, and `originalFormula_bounds` in `Properties.lean`.

**Boundary cases worth keeping explicit:**

- `CBA = 0`: all diagonal counts can be zero; the all-zero matrix also gives zero under the chosen convention.
- `CBA = 1`: requires every listed class's per-class minimum to equal one. With positive support, that means every listed class is classified with perfect precision and recall; a completely absent listed class precludes CBA = 1.
- A class that is neither actual nor predicted is assigned `(precision, recall, contribution) = (0,0,0)`; declaring such a class decreases the average whenever existing contributions have positive sum. The list of labels is part of the metric's definition.

The preceding observations are mathematically justified, but the current Lean formalization explicitly covers the general interval bound, not all of these boundary-case **iff** statements.

## 6. Objective 4: exact numerical experiments

The original repository's `src/cba.py` identifies two Figure 3.1 confusion matrices. Rows are true classes, columns are predictions:

### 6.1 Predict-all-majority classifier

```math
C_{\mathrm{majority}} =
\begin{bmatrix}
2000 & 0 & 0 \\
600 & 0 & 0 \\
600 & 0 & 0
\end{bmatrix}.
```

There are 3,200 observations and 2,000 correct predictions, so accuracy is $2000/3200=5/8=62.5\%$. Precision, recall, and CBA follow:

$$
P=(5/8,0,0),\qquad R=(1,0,0).
$$

$$
\overline P=5/24,\quad \overline R=1/3,\quad
\mathrm{CBA}=5/24\approx20.833\%.
$$

The deficit $D=0$ because $P_i\le R_i$ for every class. This is a good reminder that equality in the lower-bound theorem does **not** imply the classifier is any good.

### 6.2 Partitioned three-class classifier

```math
C_{\mathrm{partitioned}} =
\begin{bmatrix}
1000 & 500 & 500 \\
100 & 500 & 0 \\
100 & 0 & 500
\end{bmatrix}.
```

Accuracy is again $2000/3200=5/8=62.5\%$, but

$$
P=(5/6,1/2,1/2),\qquad R=(1/2,5/6,5/6),
$$

$$
\overline P=11/18,\qquad \overline R=13/18,
$$

$$
\mathrm{CBA}=(1/2+1/2+1/2)/3=1/2=50\%.
$$

The deficit is

$$
D=\min(11/18,13/18)-1/2=1/9\approx11.111\%.
$$

The classwise directions are mixed: the majority class has $P>R$, whereas both smaller classes have $R>P$. The strictness condition correctly predicts a positive deficit.

### 6.3 Simple two-class counterexample to equality

```math
C = \begin{bmatrix}
1 & 1 \\
0 & 1
\end{bmatrix},\qquad
P = (1, 1/2),\qquad R = (1/2, 1).
```

Then $\overline P=\overline R=3/4$ while $\mathrm{CBA}=1/2$. Thus taking the minimum *after* macro averaging would have returned 75%, overstating CBA by 25 percentage points.

### 6.4 Missing classes, all-zero counts, perfect classification

| Matrix | Accuracy | CBA | Key behavior |
|---|---:|---:|---|
| `[[10,0,0],[0,5,0],[0,0,0]]` | 1 | 2/3 | A declared wholly absent class reduces the average. |
| `[[0,0],[0,0]]` | 0 | 0 | The totalized division convention avoids undefined output. |
| `diag(4,5,7)` | 1 | 1 | Every declared class is predicted perfectly. |
| `[[7]]` | 1 | 1 | The definition also covers one class, even if “multi-class” applications usually start with two or three. |

### 6.5 Computational audit

The Python script uses **exact rational arithmetic** (`fractions.Fraction`, not floating-point approximations). It checks the original formula, lower bound, gap identity, equality and strictness iff criteria, and unit interval for each matrix.

| Family | Matrices checked |
|---|---:|
| All 2×2 matrices with entries in `{0,1,2,3,4,5}` | 1,296 |
| All 3×3 matrices with entries in `{0,1}` | 512 |
| All 4×4 matrices with entries in `{0,1}` | 65,536 |
| Seeded random 1–7 class matrices | 10,000 |
| Named examples above | 8 |
| **Total** | **77,352** |

**Result:** all 77,352 passed. See `results/numeric_checks.json` for detailed output and the deterministic random seed (`2013`). These finite checks are meaningful for catching definition mismatches and sign errors, but no finite sample — even an exhaustive sample of small matrices — proves the theorem for *every* finite matrix. That is what Lean's universal proof is intended to accomplish.

The original repository was consulted through its public GitHub source, but a local clone was unavailable in the authoring environment. Therefore **0 direct cross-implementation comparisons** with `src/cba.py` were executed here. Running the script from the original repository root will enable all 77,352 comparisons with its existing implementation and can detect any discrepancy.

## 7. Formalization architecture and proof status

### `Core.lean`: connect the mathematics to the dissertation

The abstract `cba`/macro definitions use arbitrary real vectors. `rowTotal`, `colTotal`, `precisionOf`, `recallOf`, `originalFormula` use natural-number matrices. Machine-checked results (in the successful user-provided build):

- `ratio_max_eq_min_div`: division by the larger of two nonnegative denominators equals the smaller of two ratios, **including zero cases**.
- `originalFormula_eq_cbaOfMatrix`: precisely Equation (1) = Equation (3).
- `cba_le_min_macro`: abstract version of Theorem 3.2.1.
- `originalFormula_le_min_macro`: same statement, specialized to the dissertation's formula.

### `Properties.lean`: derived mathematical insights

- `min_eq_half_sub_abs`: algebraic identity underlying the gap decomposition.
- `cba_gap_identity`: Equation (6).
- `abs_macro_diff_le_mean_abs_diff`: finite-sum triangle inequality.
- `macroPrecision_eq_cba_iff`, `macroRecall_eq_cba_iff`, `cba_eq_min_macro_iff`, `cba_lt_min_macro_iff`: exact equality and strictness conditions.
- `precisionOf_bounds`, `recallOf_bounds`, `originalFormula_bounds`: the unit interval.

### `Examples.lean`: concrete checks

Two Figure 3.1 matrices, an all-zero matrix, an absent class, and a two-class strict counterexample are encoded as specific finite functions `Fin k → Fin k → ℕ`. These proofs use `norm_num` to establish exact numerical equalities, not approximations. The module compiled successfully under Lean with warnings treated as errors, as recorded in `results/LEAN_STATUS.md`.

### Successful Lean verification and its precise scope

As reported in the user-supplied Windows/Lean 4.36.0 logs on 22 November 2026, `lake build --wfail` passed for `MosleyCBA.Core`, `MosleyCBA.Properties`, `MosleyCBA.Examples`, and the full project. The full build reported **18,258 jobs** and no warnings. The subsequent `lake env lean MosleyCBA/AxiomAudit.lean` command listed only the standard Lean axioms `propext`, `Classical.choice`, and `Quot.sound` for nine central theorem statements; none listed `sorryAx`. The exact command outcomes and theorem names are documented in [`results/LEAN_STATUS.md`](results/LEAN_STATUS.md).

This constitutes evidence of machine-checked proofs of the **encoded** definitions, mathematical identities, inequalities, and numerical examples. It does not establish external empirical validity, a new scientific claim of priority, or the full dissertation's experimental conclusions. The proofs were run in the user's environment; the document-authoring environment did not independently rerun Lean. A public GitHub Actions success URL and immutable commit ID would be valuable additional reproducibility evidence before publication.

## 8. Further questions for a subsequent formal-verification version

These are promising follow-on results but **not proofs claimed by this verified project**:

1. **Label permutation invariance.** Simultaneously permuting rows and columns leaves CBA unchanged.
2. **Scale invariance.** Multiplying all confusion-matrix entries by any positive integer leaves CBA unchanged.
3. **Exact zero and perfect-one characterizations.** Prove which confusion matrices attain the extrema under the missing-class convention.
4. **Sensitivity to declared class sets.** Formalize how appending unused classes rescales CBA and highlight implications for comparing reports across different label universes.
5. **Metric comparisons.** Derive precise comparisons to macro-F1 and other metrics where mathematically valid, explicitly separating provable bounds from empirical performance claims.
6. **Weighted CBA.** Study whether the original inequalities survive class weighting and specify precisely which weight choices preserve them.
7. **Machine-verifying numerical parity with other languages.** Export certified examples and cross-check Python, R, and PyCM implementation conventions.

## 9. Reproducibility checklist and citation

A reproducible paper/repository note should include:

- The exact confusion-matrix orientation (actual = rows; predicted = columns), class index, and zero-denominator policy.
- Equation 3.4 with an explicit statement that empty declared classes remain in the average.
- The lower-bound theorem **as an inequality**.
- Distinction between Theorem 3.2.1 (Mosley, 2013) and the additional gap/equality theorems (this companion).
- Exact rational Figure 3.1 values and the independent computational check count.
- The user-supplied warning-free Lean build and axiom audit, the pinned toolchain versions, and (when available) a public CI URL and exact commit ID.

**Primary citation:** Mosley, Lawrence S. D. (2013), *A Balanced Approach to the Multi-Class Imbalance Problem*, PhD dissertation, Iowa State University. [https://doi.org/10.31274/etd-180810-3375](https://doi.org/10.31274/etd-180810-3375).

**Implementation:** [Omni-Analytics-Group public repository](https://github.com/Omni-Analytics-Group/a_balanced_approach_to_the_multi-class_imbalance_problem), `src/cba.py`. Note that this detailed companion documents the ideas and proof process; it does not rewrite or supersede the original dissertation.
