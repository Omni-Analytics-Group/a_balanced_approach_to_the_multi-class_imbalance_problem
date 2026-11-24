module

public import Mathlib

/-!
# Mosley (2013): Class Balance Accuracy, core formalization

A finite, *nonempty* index type represents the classes. The confusion matrix
has natural-number entries, hence cannot contain negative counts. In Lean's
real-number field, `0 / 0 = 0`; this is also the convention used by the
repository's reference implementation at `src/cba.py`.

The main results in this module are:
- `originalFormula_eq_cbaOfMatrix`: Equation 3.4 equals the mean of per-class
  minima of precision and recallScores, including empty classes.
- `originalFormula_le_min_macro`: Mosley (2013), Theorem 3.2.1.

No `sorry`, `admit`, or custom axioms are intended in this file.
-/

public section

open scoped BigOperators

namespace MosleyCBA

variable {ι : Type*} [Fintype ι] [Nonempty ι]

/-- The 2013 definition, expressed using per-class precision and recall. -/
@[expose] noncomputable def cba (precision recallScores : ι → ℝ) : ℝ :=
  (∑ i, min (precision i) (recallScores i)) / (Fintype.card ι : ℝ)

/-- Unweighted class-average precision. -/
@[expose] noncomputable def macroPrecision (precision : ι → ℝ) : ℝ :=
  (∑ i, precision i) / (Fintype.card ι : ℝ)

/-- Unweighted class-average recall (often called balanced accuracy). -/
@[expose] noncomputable def macroRecall (recallScores : ι → ℝ) : ℝ :=
  (∑ i, recallScores i) / (Fintype.card ι : ℝ)

private theorem classCount_pos : (0 : ℝ) < (Fintype.card ι : ℝ) := by
  exact_mod_cast (Fintype.card_pos (α := ι))

/-- Abstract version of Theorem 3.2.1: the mean of the minima is at most
    the minimum of the means. No probability assumptions are needed. -/
theorem cba_le_min_macro (precision recallScores : ι → ℝ) :
    cba precision recallScores ≤
      min (macroPrecision precision) (macroRecall recallScores) := by
  have hn : (0 : ℝ) < (Fintype.card ι : ℝ) := classCount_pos
  unfold cba macroPrecision macroRecall
  apply le_min
  · apply (div_le_div_iff_of_pos_right hn).2
    apply Finset.sum_le_sum
    intro i _
    exact min_le_left (precision i) (recallScores i)
  · apply (div_le_div_iff_of_pos_right hn).2
    apply Finset.sum_le_sum
    intro i _
    exact min_le_right (precision i) (recallScores i)

/-- Ground-truth (row) total of a nonnegative confusion matrix. -/
@[expose] noncomputable def rowTotal (M : ι → ι → ℕ) (i : ι) : ℝ :=
  ∑ j, (M i j : ℝ)

/-- Predicted (column) total of a nonnegative confusion matrix. -/
@[expose] noncomputable def colTotal (M : ι → ι → ℕ) (i : ι) : ℝ :=
  ∑ j, (M j i : ℝ)

/-- Per-class precision, including the convention `0 / 0 = 0`. -/
@[expose] noncomputable def precisionOf (M : ι → ι → ℕ) (i : ι) : ℝ :=
  (M i i : ℝ) / colTotal M i

/-- Per-class recallScores, including the convention `0 / 0 = 0`. -/
@[expose] noncomputable def recallOf (M : ι → ι → ℕ) (i : ι) : ℝ :=
  (M i i : ℝ) / rowTotal M i

/-- CBA written as the average of `min(precision, recallScores)`. -/
@[expose] noncomputable def cbaOfMatrix (M : ι → ι → ℕ) : ℝ :=
  cba (precisionOf M) (recallOf M)

/-- CBA in Mosley (2013), Equation 3.4: diagonal / max(row, column). -/
@[expose] noncomputable def originalFormula (M : ι → ι → ℕ) : ℝ :=
  (∑ i, (M i i : ℝ) / max (rowTotal M i) (colTotal M i)) /
    (Fintype.card ι : ℝ)

omit [Nonempty ι] in
/-- The diagonal entry cannot exceed its row total. -/
theorem diagonal_le_row (M : ι → ι → ℕ) (i : ι) :
    (M i i : ℝ) ≤ rowTotal M i := by
  unfold rowTotal
  exact Finset.single_le_sum
    (fun j _ => (Nat.cast_nonneg (M i j))) (Finset.mem_univ i)

omit [Nonempty ι] in
/-- The diagonal entry cannot exceed its column total. -/
theorem diagonal_le_column (M : ι → ι → ℕ) (i : ι) :
    (M i i : ℝ) ≤ colTotal M i := by
  unfold colTotal
  exact Finset.single_le_sum
    (fun j _ => (Nat.cast_nonneg (M j i))) (Finset.mem_univ i)

/-- When the numerator is nonnegative and no larger than either denominator,
    division by their maximum is the minimum of the two ratios.
    The zero-denominator cases are proved rather than assumed away. -/
theorem ratio_max_eq_min_div (d a b : ℝ)
    (hd : 0 ≤ d) (hda : d ≤ a) (hdb : d ≤ b) :
    d / max a b = min (d / a) (d / b) := by
  rcases le_total a b with hab | hba
  · rw [max_eq_right hab]
    by_cases ha : a = 0
    · have hd0 : d = 0 := by
        apply le_antisymm
        · simpa [ha] using hda
        · exact hd
      simp [hd0]
    · have ha0 : (0 : ℝ) ≤ a := le_trans hd hda
      have haPos : 0 < a := lt_of_le_of_ne ha0 (Ne.symm ha)
      have hle : d / b ≤ d / a :=
        div_le_div_of_nonneg_left hd haPos hab
      exact (min_eq_right hle).symm
  · rw [max_eq_left hba]
    by_cases hb : b = 0
    · have hd0 : d = 0 := by
        apply le_antisymm
        · simpa [hb] using hdb
        · exact hd
      simp [hd0]
    · have hb0 : (0 : ℝ) ≤ b := le_trans hd hdb
      have hbPos : 0 < b := lt_of_le_of_ne hb0 (Ne.symm hb)
      have hle : d / a ≤ d / b :=
        div_le_div_of_nonneg_left hd hbPos hba
      exact (min_eq_left hle).symm

omit [Nonempty ι] in
/-- At each class, the dissertation's fraction is the smaller of its
    precision and recallScores. -/
theorem originalTerm_eq_min (M : ι → ι → ℕ) (i : ι) :
    (M i i : ℝ) / max (rowTotal M i) (colTotal M i) =
      min (precisionOf M i) (recallOf M i) := by
  have h := ratio_max_eq_min_div
    (M i i : ℝ) (rowTotal M i) (colTotal M i)
    (Nat.cast_nonneg _) (diagonal_le_row M i) (diagonal_le_column M i)
  calc
    (M i i : ℝ) / max (rowTotal M i) (colTotal M i) =
        min ((M i i : ℝ) / rowTotal M i)
            ((M i i : ℝ) / colTotal M i) := h
    _ = min (precisionOf M i) (recallOf M i) := by
      simpa only [precisionOf, recallOf] using
        (min_comm ((M i i : ℝ) / rowTotal M i)
                  ((M i i : ℝ) / colTotal M i))

omit [Nonempty ι] in
/-- Formal identification of Equation 3.4 with the per-class min formulation. -/
theorem originalFormula_eq_cbaOfMatrix (M : ι → ι → ℕ) :
    originalFormula M = cbaOfMatrix M := by
  have hsum :
      (∑ i, (M i i : ℝ) / max (rowTotal M i) (colTotal M i)) =
      (∑ i, min (precisionOf M i) (recallOf M i)) := by
    apply Finset.sum_congr rfl
    intro i _
    exact originalTerm_eq_min M i
  unfold originalFormula cbaOfMatrix cba
  rw [hsum]

/-- Theorem 3.2.1 for any nonempty finite confusion matrix. -/
theorem originalFormula_le_min_macro (M : ι → ι → ℕ) :
    originalFormula M ≤
      min (macroPrecision (precisionOf M))
          (macroRecall (recallOf M)) := by
  rw [originalFormula_eq_cbaOfMatrix]
  exact cba_le_min_macro (precisionOf M) (recallOf M)

end MosleyCBA

namespace MosleyCBA

variable {ι : Type*} [Fintype ι] [Nonempty ι]

/-- Ordinary overall accuracy. For an all-zero matrix it is defined to be zero. -/
@[expose] noncomputable def accuracyOfMatrix (M : ι → ι → ℕ) : ℝ :=
  (∑ i, (M i i : ℝ)) / (∑ i, rowTotal M i)

end MosleyCBA

end -- public section
