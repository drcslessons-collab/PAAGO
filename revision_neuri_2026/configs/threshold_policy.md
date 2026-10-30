# Threshold-selection policy

Candidate thresholds comprise 200 values from 0.001 to 0.50, 50 values from 0.50 to 0.99, and 199 quantiles of validation probabilities.

Validation-F2 selection requires sensitivity >= 0.55 when feasible.

Ties are resolved by maximizing, in order: the target F-score, validation F1, specificity, and then choosing the lower threshold. The selected threshold is frozen before test and external evaluation.
