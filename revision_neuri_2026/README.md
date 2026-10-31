# PAAGO Neuroscience Informatics Final Revision

This directory contains the anonymized reproducibility materials corresponding to the final revised manuscript submitted to *Neuroscience Informatics*.

Version: `v1.1.1-neuri-final-revision`

## Audited evaluation cohorts

| Dataset | Patients | Windows | Ictal windows | Seizures | Exposure |
|---|---:|---:|---:|---:|---:|
| CHB-MIT held-out test | 4 | 76,554 | 344 | 34 | 106.05 interictal h |
| Siena external evaluation | 14 | 101,479 | 984 | 47 | 139.20 interictal h |

The analysis contains 15 canonical checkpoints and 45 operating evaluations: three loss families, three operating-point policies, and five matched seeds.

## Important terminology

Validation-F1 and validation-F2 are **operating-point-selection policies**, not probability-calibration procedures. Policies derived from a shared checkpoint reuse the same continuous scores and therefore have identical ROC-AUC and average precision within each family and seed.

Average precision was computed with `sklearn.metrics.average_precision_score`; it was not obtained by trapezoidal integration of a precision-recall curve.

## Main updates in v1.1.1

- adds paired Cohen's dz to CHB-MIT and Siena statistical outputs;
- adds conditional latency quartiles and contributing detection counts;
- expands cohort and patient-partition provenance;
- documents unavailable historical fields without retrospective reconstruction;
- clarifies that Siena time-in-alarm was unavailable in the archived external export;
- aligns loss and architecture documentation with the implemented softmax classifier and SmoothL1 auxiliary loss.

## Reproduction

```bash
python scripts/recompute_corrected_chb.py
python scripts/recompute_siena_corrected47.py
python scripts/verify_revision_outputs.py
```

Raw EEG recordings and trained checkpoints are not redistributed. Obtain CHB-MIT and Siena from PhysioNet under their respective data-use conditions. Reproduction of score-based analyses requires the canonical score inputs described in the scripts and provenance files.

The task evaluated here is ictal seizure detection, not preictal seizure forecasting.
