module

public import MosleyCBA.Properties

/-!
# Exact executable-looking examples as Lean theorems

These state the exact Figure 3.1 values from `src/cba.py` and additional
edge-case matrices. Proof attempts rely on `norm_num` and finite sums.
They are deliberately in a separate module so the user can send a focused
compiler error log without hiding the more general theory.
-/

public section

namespace MosleyCBA

/-- Figure 3.1: always predicts the majority (class 0). -/
@[expose] def figure31Majority (i j : Fin 3) : ℕ :=
  if j = 0 then (if i = 0 then 2000 else 600) else 0

/-- Figure 3.1: predicts all three classes, overall accuracy still 62.5%. -/
@[expose] def figure31Partitioned (i j : Fin 3) : ℕ :=
  if i = 0 then (if j = 0 then 1000 else 500)
  else if i = 1 then (if j = 0 then 100 else if j = 1 then 500 else 0)
  else (if j = 0 then 100 else if j = 2 then 500 else 0)

/-- Illustrates strictness of CBA <= min(macro precision, macro recall). -/
@[expose] def binaryCounterexample (i j : Fin 2) : ℕ :=
  if i = 0 then (if j = 0 then 1 else 1)
  else (if j = 0 then 0 else 1)

/-- The third class is listed but has neither observations nor predictions. -/
@[expose] def absentClass (i j : Fin 3) : ℕ :=
  if i = j then (if i = 0 then 10 else if i = 1 then 5 else 0) else 0

/-- Every class is absent: by convention the score is zero, not undefined. -/
@[expose] def allZero (_i _j : Fin 2) : ℕ := 0

/-- Numerical results are *exact* rational equalities in the real numbers. -/
theorem figure31_majority_accuracy :
    accuracyOfMatrix figure31Majority = (5 : ℝ) / 8 := by
  norm_num [accuracyOfMatrix, rowTotal, figure31Majority, Fin.sum_univ_succ]

theorem figure31_majority_cba :
    originalFormula figure31Majority = (5 : ℝ) / 24 := by
  norm_num [originalFormula, rowTotal, colTotal, figure31Majority,
    Fin.sum_univ_succ]

theorem figure31_partitioned_accuracy :
    accuracyOfMatrix figure31Partitioned = (5 : ℝ) / 8 := by
  norm_num [accuracyOfMatrix, rowTotal, figure31Partitioned, Fin.sum_univ_succ]

theorem figure31_partitioned_cba :
    originalFormula figure31Partitioned = (1 : ℝ) / 2 := by
  norm_num [originalFormula, rowTotal, colTotal, figure31Partitioned,
    Fin.sum_univ_succ]

theorem absent_class_cba :
    originalFormula absentClass = (2 : ℝ) / 3 := by
  norm_num [originalFormula, rowTotal, colTotal, absentClass, Fin.sum_univ_succ]

theorem all_zero_cba : originalFormula allZero = 0 := by
  simp [originalFormula, rowTotal, colTotal, allZero]

theorem binary_counterexample_cba :
    originalFormula binaryCounterexample = (1 : ℝ) / 2 := by
  norm_num [originalFormula, rowTotal, colTotal, binaryCounterexample,
    Fin.sum_univ_succ]

theorem binary_counterexample_strict :
    originalFormula binaryCounterexample <
      min (macroPrecision (precisionOf binaryCounterexample))
          (macroRecall (recallOf binaryCounterexample)) := by
  norm_num [originalFormula, macroPrecision, macroRecall, precisionOf,
    recallOf, rowTotal, colTotal, binaryCounterexample,
    Fin.sum_univ_succ]

end MosleyCBA

end -- public section
