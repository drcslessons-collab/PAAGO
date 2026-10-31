# Operating-point-selection policy

Candidate thresholds comprise 200 values from 0.001 to 0.50, 50 values from 0.50 to 0.99, and 199 quantiles of the validation probabilities.

Validation-F2 selection requires sensitivity >= 0.55 when feasible.

Ties are resolved by maximizing, in order: the target F-score, validation F1, specificity, and then choosing the lower threshold. The selected operating point is frozen before test and external evaluation.

This procedure changes binary decisions and threshold-dependent metrics. It does not calibrate predicted probabilities and cannot change ROC-AUC or average precision when the continuous scores are shared.
