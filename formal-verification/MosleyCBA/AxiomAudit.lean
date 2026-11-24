module

import MosleyCBA.Examples

/-!
Run after successful build with
  lake env lean MosleyCBA/AxiomAudit.lean

For a finished proof, `#print axioms` should NOT show `sorryAx` or any
custom project axiom. Standard Lean/Mathlib axioms such as `propext`,
`Quot.sound`, and `Classical.choice` are acceptable.
-/

#print axioms MosleyCBA.originalFormula_eq_cbaOfMatrix
#print axioms MosleyCBA.originalFormula_le_min_macro
#print axioms MosleyCBA.cba_gap_identity
#print axioms MosleyCBA.abs_macro_diff_le_mean_abs_diff
#print axioms MosleyCBA.cba_eq_min_macro_iff
#print axioms MosleyCBA.cba_lt_min_macro_iff
#print axioms MosleyCBA.originalFormula_bounds
#print axioms MosleyCBA.figure31_majority_cba
#print axioms MosleyCBA.figure31_partitioned_cba
