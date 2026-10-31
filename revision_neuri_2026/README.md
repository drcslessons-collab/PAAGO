# PAAGO Neuroscience Informatics Major Revision

This directory contains the corrected and expanded reproducibility materials associated with the Neuroscience Informatics major revision.

Version: `v1.1.0-neuri-major-revision`

## Audited evaluation cohorts

| Dataset | Patients | Windows | Ictal windows | Seizures |
|---|---:|---:|---:|---:|
| CHB-MIT test | 4 | 76,554 | 344 | 34 |
| Siena | 14 | 101,479 | 984 | 47 |

The revision contains 15 canonical checkpoints and 45 operating evaluations (three loss families, three threshold policies, and five seeds).

## Reproduction

```bash
python scripts/recompute_corrected_chb.py
python scripts/recompute_siena_corrected47.py
python scripts/verify_revision_outputs.py
```

Raw EEG files are not redistributed. Obtain CHB-MIT and Siena from PhysioNet under their respective data-use conditions.

The task evaluated here is ictal seizure detection, not preictal seizure forecasting.
