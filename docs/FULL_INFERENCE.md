# Full inference

The included bundle guarantees analysis-level reproducibility from archived
out-of-sample predictions. Full inference additionally requires:

1. Siena Scalp EEG v1.0.0 EDF files obtained from PhysioNet;
2. the five trained checkpoints for each evaluated method;
3. the original PAAGO model/inference implementation;
4. 21 bipolar derivations, 256 Hz target sampling, 10 s windows and 5 s stride.

Keep raw data under `data/raw/` and checkpoints under `checkpoints/`; both are
ignored by Git. Verify 14 patients, 41 EDF files and 47 seizures before running.
The corrected metadata is in `data/reference/` and its provenance archive is in
`data/source_archives/`.

Because checkpoints are not redistributed here, do not describe a successful
`make reproduce` run as retraining or as full end-to-end inference.

