module

public import MosleyCBA.Core

/-!
# Strengthened properties of Class Balance Accuracy

These theorems are *mathematical extensions* of the dissertation's core bound,
not claims that the dissertation explicitly contains these stronger results.

Lean 4 + Mathlib. This draft requires compilation on a Lean-equipped machine
before its statements can be advertised as kernel-checked.
-/

public section

open scoped BigOperators

namespace MosleyCBA

variable {ι : Type*} [Fintype ι] [Nonempty ι]

private theorem classCount_pos' : (0 : ℝ) < (Fintype.card ι : ℝ) := by
  exact_mod_cast (Fintype.card_pos (α := ι))

/-- Purely real-variable version: the minimum is a simple absolute-value expression. -/
theorem min_eq_half_sub_abs (a b : ℝ) :
    min a b = (a + b - |a - b|) / 2 := by
  rcases le_total a b with hab | hba
  · rw [min_eq_left hab, abs_of_nonpos (sub_nonpos.mpr hab)]
    ring
  · rw [min_eq_right hba, abs_of_nonneg (sub_nonneg.mpr hba)]
    ring

omit [Nonempty ι] in
/-- Exact CBA gap decomposition:

min(macro precision, macro recall) - CBA
  = (mean(abs(precision_i-recall_i)) - abs(macro precision-macro recall))/2.

The equality is true for arbitrary real-valued vectors, even those that are
not meaningful precision/recall vectors.
-/
theorem cba_gap_identity (p r : ι → ℝ) :
    min (macroPrecision p) (macroRecall r) - cba p r =
      ((∑ i, |p i - r i|) / (Fintype.card ι : ℝ) -
        |macroPrecision p - macroRecall r|) / 2 := by
  have hsum :
      (∑ i, min (p i) (r i)) =
        ((∑ i, p i) + (∑ i, r i) - (∑ i, |p i - r i|)) / 2 := by
    calc
      (∑ i, min (p i) (r i)) =
          ∑ i, ((p i + r i - |p i - r i|) / 2) := by
        apply Finset.sum_congr rfl
        intro i _
        exact min_eq_half_sub_abs (p i) (r i)
      _ = ((∑ i, p i) + (∑ i, r i) - (∑ i, |p i - r i|)) / 2 := by
        rw [← Finset.sum_div, Finset.sum_sub_distrib, Finset.sum_add_distrib]
  rw [min_eq_half_sub_abs]
  unfold macroPrecision macroRecall cba
  rw [hsum]
  ring

/-- The gap is nonnegative, another expression of Theorem 3.2.1. -/
theorem cba_gap_nonneg (p r : ι → ℝ) :
    0 ≤ min (macroPrecision p) (macroRecall r) - cba p r := by
  exact sub_nonneg.mpr (cba_le_min_macro p r)

/-- The mean absolute classwise precision/recall difference is at least the
    absolute difference between the means (triangle inequality). -/
theorem abs_macro_diff_le_mean_abs_diff (p r : ι → ℝ) :
    |macroPrecision p - macroRecall r| ≤
      (∑ i, |p i - r i|) / (Fintype.card ι : ℝ) := by
  have hn : (0 : ℝ) < (Fintype.card ι : ℝ) := classCount_pos'
  have htriangle :
      |∑ i, (p i - r i)| ≤ ∑ i, |p i - r i| := by
    exact Finset.abs_sum_le_sum_abs _ _
  have hnorm :
      |macroPrecision p - macroRecall r| =
        |∑ i, (p i - r i)| / (Fintype.card ι : ℝ) := by
    unfold macroPrecision macroRecall
    rw [← sub_div, ← Finset.sum_sub_distrib, abs_div, abs_of_pos hn]
  rw [hnorm]
  exact (div_le_div_iff_of_pos_right hn).2 htriangle

omit [Nonempty ι] in
/-- If each class's precision is at most its recall, CBA is macro precision. -/
theorem cba_eq_macroPrecision_of_le (p r : ι → ℝ)
    (hp : ∀ i, p i ≤ r i) :
    cba p r = macroPrecision p := by
  unfold cba macroPrecision
  have hsum : (∑ i, min (p i) (r i)) = ∑ i, p i := by
    apply Finset.sum_congr rfl
    intro i _
    exact min_eq_left (hp i)
  rw [hsum]

omit [Nonempty ι] in
/-- If each class's recall is at most its precision, CBA is macro recall. -/
theorem cba_eq_macroRecall_of_le (p r : ι → ℝ)
    (hr : ∀ i, r i ≤ p i) :
    cba p r = macroRecall r := by
  unfold cba macroRecall
  have hsum : (∑ i, min (p i) (r i)) = ∑ i, r i := by
    apply Finset.sum_congr rfl
    intro i _
    exact min_eq_right (hr i)
  rw [hsum]

/-- The existing 'if each precision <= recall' sufficient condition. -/
theorem macroPrecision_eq_cba_iff (p r : ι → ℝ) :
    macroPrecision p = cba p r ↔ ∀ i, p i ≤ r i := by
  constructor
  · intro heq i
    have hn : (Fintype.card ι : ℝ) ≠ 0 := ne_of_gt classCount_pos'
    have hnum :
        (∑ j, p j) = (∑ j, min (p j) (r j)) := by
      have hmul := congrArg (fun x : ℝ => x * (Fintype.card ι : ℝ)) heq
      change
        ((∑ j, p j) / (Fintype.card ι : ℝ)) * (Fintype.card ι : ℝ) =
        ((∑ j, min (p j) (r j)) / (Fintype.card ι : ℝ)) *
          (Fintype.card ι : ℝ) at hmul
      field_simp [hn] at hmul
      exact hmul
    have hsum : (∑ j, (p j - min (p j) (r j))) = 0 := by
      rw [Finset.sum_sub_distrib, hnum, sub_self]
    have hterm : p i - min (p i) (r i) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg
        (fun j _ => sub_nonneg.mpr (min_le_left (p j) (r j)))).1
          hsum i (Finset.mem_univ i)
    have hmin : p i = min (p i) (r i) := sub_eq_zero.mp hterm
    calc
      p i = min (p i) (r i) := hmin
      _ ≤ r i := min_le_right (p i) (r i)
  · intro hp
    exact (cba_eq_macroPrecision_of_le p r hp).symm

/-- Symmetric characterization for macro recall. -/
theorem macroRecall_eq_cba_iff (p r : ι → ℝ) :
    macroRecall r = cba p r ↔ ∀ i, r i ≤ p i := by
  constructor
  · intro heq i
    have hn : (Fintype.card ι : ℝ) ≠ 0 := ne_of_gt classCount_pos'
    have hnum :
        (∑ j, r j) = (∑ j, min (p j) (r j)) := by
      have hmul := congrArg (fun x : ℝ => x * (Fintype.card ι : ℝ)) heq
      change
        ((∑ j, r j) / (Fintype.card ι : ℝ)) * (Fintype.card ι : ℝ) =
        ((∑ j, min (p j) (r j)) / (Fintype.card ι : ℝ)) *
          (Fintype.card ι : ℝ) at hmul
      field_simp [hn] at hmul
      exact hmul
    have hsum : (∑ j, (r j - min (p j) (r j))) = 0 := by
      rw [Finset.sum_sub_distrib, hnum, sub_self]
    have hterm : r i - min (p i) (r i) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg
        (fun j _ => sub_nonneg.mpr (min_le_right (p j) (r j)))).1
          hsum i (Finset.mem_univ i)
    have hmin : r i = min (p i) (r i) := sub_eq_zero.mp hterm
    calc
      r i = min (p i) (r i) := hmin
      _ ≤ p i := min_le_left (p i) (r i)
  · intro hr
    exact (cba_eq_macroRecall_of_le p r hr).symm

/-- **Complete equality criterion**: CBA reaches the smaller macro average
iff all per-class precision/recall comparisons have the same orientation.
Zeros and ties are permitted; mixed strict orientations give a strict gap.
-/
theorem cba_eq_min_macro_iff (p r : ι → ℝ) :
    cba p r = min (macroPrecision p) (macroRecall r) ↔
      (∀ i, p i ≤ r i) ∨ (∀ i, r i ≤ p i) := by
  constructor
  · intro heq
    rcases le_total (macroPrecision p) (macroRecall r) with hp | hr
    · left
      have hmp : macroPrecision p = cba p r := by
        calc
          macroPrecision p = min (macroPrecision p) (macroRecall r) :=
            (min_eq_left hp).symm
          _ = cba p r := heq.symm
      exact (macroPrecision_eq_cba_iff p r).1 hmp
    · right
      have hmr : macroRecall r = cba p r := by
        calc
          macroRecall r = min (macroPrecision p) (macroRecall r) :=
            (min_eq_right hr).symm
          _ = cba p r := heq.symm
      exact (macroRecall_eq_cba_iff p r).1 hmr
  · rintro (hp | hr)
    · have h := cba_le_min_macro p r
      rw [cba_eq_macroPrecision_of_le p r hp] at h ⊢
      exact le_antisymm h (min_le_left _ _)
    · have h := cba_le_min_macro p r
      rw [cba_eq_macroRecall_of_le p r hr] at h ⊢
      exact le_antisymm h (min_le_right _ _)

/-- Corollary: a strict deficit occurs exactly when at least one class has
precision < recall and another has recall < precision. -/
theorem cba_lt_min_macro_iff (p r : ι → ℝ) :
    cba p r < min (macroPrecision p) (macroRecall r) ↔
      (∃ i, p i < r i) ∧ (∃ j, r j < p j) := by
  have hbound := cba_le_min_macro p r
  have heq := cba_eq_min_macro_iff p r
  constructor
  · intro h
    have hne : ¬((∀ i, p i ≤ r i) ∨ (∀ i, r i ≤ p i)) := by
      intro hor
      exact (ne_of_lt h) (heq.mpr hor)
    push Not at hne
    rcases hne with ⟨h1, h2⟩
    constructor
    · rcases h2 with ⟨i, hi⟩
      exact ⟨i, hi⟩
    · rcases h1 with ⟨j, hj⟩
      exact ⟨j, hj⟩
  · rintro ⟨⟨i, hi⟩, ⟨j, hj⟩⟩
    have hne : cba p r ≠ min (macroPrecision p) (macroRecall r) := by
      intro h
      rcases heq.mp h with hp | hr
      · exact (not_lt_of_ge (hp j)) hj
      · exact (not_lt_of_ge (hr i)) hi
    exact lt_of_le_of_ne hbound hne

omit [Nonempty ι] in
/-- CBA is nonnegative when both input vectors are nonnegative. -/
theorem cba_nonneg_of_nonneg (p r : ι → ℝ)
    (hp : ∀ i, 0 ≤ p i) (hr : ∀ i, 0 ≤ r i) :
    0 ≤ cba p r := by
  unfold cba
  apply div_nonneg
  · apply Finset.sum_nonneg
    intro i _
    exact le_min (hp i) (hr i)
  · exact Nat.cast_nonneg _

/-- Every input component <= 1 gives CBA <= 1. -/
theorem cba_le_one_of_le_one (p r : ι → ℝ) (hp : ∀ i, p i ≤ 1) :
    cba p r ≤ 1 := by
  have hn : (0 : ℝ) < (Fintype.card ι : ℝ) := classCount_pos'
  have hsum :
      (∑ i, min (p i) (r i)) ≤ ∑ _i : ι, (1 : ℝ) := by
    apply Finset.sum_le_sum
    intro i _
    exact le_trans (min_le_left (p i) (r i)) (hp i)
  calc
    cba p r ≤ (∑ _i : ι, (1 : ℝ)) / (Fintype.card ι : ℝ) := by
      unfold cba
      exact (div_le_div_iff_of_pos_right hn).2 hsum
    _ = 1 := by
      simp [ne_of_gt hn]

omit [Nonempty ι] in
/-- If a natural-number confusion-matrix column is empty, Lean's 0/0=0
convention ensures the corresponding precision is zero; otherwise both
precision and recall lie in [0,1]. -/
theorem precisionOf_bounds (M : ι → ι → ℕ) (i : ι) :
    0 ≤ precisionOf M i ∧ precisionOf M i ≤ 1 := by
  have hd : (0 : ℝ) ≤ (M i i : ℝ) := Nat.cast_nonneg _
  have hle := diagonal_le_column M i
  have ht : 0 ≤ colTotal M i := le_trans hd hle
  by_cases h0 : colTotal M i = 0
  · simp [precisionOf, h0]
  · have hpos : 0 < colTotal M i := lt_of_le_of_ne ht (Ne.symm h0)
    constructor
    · exact div_nonneg hd (le_of_lt hpos)
    · exact (div_le_one hpos).2 hle

omit [Nonempty ι] in
theorem recallOf_bounds (M : ι → ι → ℕ) (i : ι) :
    0 ≤ recallOf M i ∧ recallOf M i ≤ 1 := by
  have hd : (0 : ℝ) ≤ (M i i : ℝ) := Nat.cast_nonneg _
  have hle := diagonal_le_row M i
  have ht : 0 ≤ rowTotal M i := le_trans hd hle
  by_cases h0 : rowTotal M i = 0
  · simp [recallOf, h0]
  · have hpos : 0 < rowTotal M i := lt_of_le_of_ne ht (Ne.symm h0)
    constructor
    · exact div_nonneg hd (le_of_lt hpos)
    · exact (div_le_one hpos).2 hle

/-- For every (nonempty-class-index) natural-number confusion matrix,
CBA lies in the closed interval [0,1], even if all counts are zero. -/
theorem cbaOfMatrix_bounds (M : ι → ι → ℕ) :
    0 ≤ cbaOfMatrix M ∧ cbaOfMatrix M ≤ 1 := by
  unfold cbaOfMatrix
  constructor
  · apply cba_nonneg_of_nonneg
      (precisionOf M) (recallOf M)
    · intro i
      exact (precisionOf_bounds M i).1
    · intro i
      exact (recallOf_bounds M i).1
  · apply cba_le_one_of_le_one
    intro i
    exact (precisionOf_bounds M i).2

/-- The dissertation's original Equation 3.4 is in [0, 1]. -/
theorem originalFormula_bounds (M : ι → ι → ℕ) :
    0 ≤ originalFormula M ∧ originalFormula M ≤ 1 := by
  rw [originalFormula_eq_cbaOfMatrix]
  exact cbaOfMatrix_bounds M

end MosleyCBA

end -- public section
