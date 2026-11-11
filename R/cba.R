# Class Balance Accuracy (CBA), from L. Mosley (2013), "A Balanced Approach to
# the Multi-class Imbalance Problem", PhD thesis, Iowa State University, Eq. 3.4.
#
# `cm` is a square confusion matrix or table with actual classes in rows and
# predicted classes in columns, for example table(actual, predicted) built from
# two factors that share the same levels.

validated_matrix <- function(cm) {
  cm <- as.matrix(cm)
  if (nrow(cm) != ncol(cm)) stop("confusion matrix must be square")
  if (anyNA(cm) || any(cm < 0)) stop("confusion matrix counts must be non-negative numbers")
  cm
}

# A class that is never observed and never predicted contributes 0.
per_class_cba <- function(cm) {
  cm <- validated_matrix(cm)
  denominator <- pmax(rowSums(cm), colSums(cm))
  ifelse(denominator > 0, diag(cm) / denominator, 0)
}

class_balance_accuracy <- function(cm) mean(per_class_cba(cm))

balanced_accuracy <- function(cm) {
  cm <- validated_matrix(cm)
  totals <- rowSums(cm)
  mean(ifelse(totals > 0, diag(cm) / totals, 0))
}

if (sys.nframe() == 0) {
  # Figure 3.1 of the dissertation: same accuracy, very different models.
  all_red <- matrix(c(2000, 0, 0, 600, 0, 0, 600, 0, 0), nrow = 3, byrow = TRUE)
  partitioned <- matrix(c(1000, 500, 500, 100, 500, 0, 100, 0, 500), nrow = 3, byrow = TRUE)
  stopifnot(abs(class_balance_accuracy(all_red) - 0.2083333) < 1e-6)
  stopifnot(abs(class_balance_accuracy(partitioned) - 0.5) < 1e-12)
  stopifnot(class_balance_accuracy(partitioned) <= balanced_accuracy(partitioned))
  stopifnot(inherits(try(class_balance_accuracy(matrix(c(NA, 1, 1, 1), 2)), silent = TRUE), "try-error"))
  stopifnot(inherits(try(balanced_accuracy(matrix(1:6, 2)), silent = TRUE), "try-error"))
  cat(sprintf("all-red CBA = %.3f, partitioned CBA = %.3f\n",
              class_balance_accuracy(all_red), class_balance_accuracy(partitioned)))
}
