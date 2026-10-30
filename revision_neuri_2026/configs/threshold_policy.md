# Threshold-selection policy

Candidate thresholds comprise:

- 200 values from 0.001 to 0.50;
- 50 values from 0.50 to 0.99;
- 199 quantiles of the validation probabilities.

Validation-F2 selection requires sensitivity >= 0.55 when feasible.

Ties are resolved deterministically by maximizing, in order:

1. the target F-score;
2. validation F1;
3. specificity;
4. the lower threshold.

The selected threshold is frozen before test and external evaluation.
