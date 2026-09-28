# PAAGO v6.3 reproducibility materials

Companion materials for **Patient-Independent Seizure Detection with PAAGO**.
This repository reproduces the published tables, summary statistics, audit trail,
and figures from archived out-of-sample predictions. It does **not** redistribute
raw EEG recordings or model checkpoints.

## Reproducibility levels

| Level | Included | Command |
|---|---|---|
| Results/figures | Yes; runs entirely from this repository | `make reproduce` |
| Integrity audit | Yes; validates archives, 14 patients, 41 EDFs and 47 events | `make verify` |
| Full inference | Supported when the user supplies Siena EDFs and checkpoints | See `docs/FULL_INFERENCE.md` |
| Training | Not claimed by this bundle; requires the training repository and CHB-MIT access | See `docs/DATA_ACCESS.md` |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make verify
make reproduce
pytest -q
```

Generated files are written to `outputs/reproduced/`. The command creates:

- per-run and mean±SD metric tables;
- corrected Siena external-validation table used in the manuscript;
- sensitivity/false-alarm and ROC/PR figures;
- an input-integrity and provenance manifest.

## Data included

`data/source_archives/` contains only derived prediction tables, evaluation
summaries, and corrected event metadata. Paths appearing inside CSV files are
historical provenance strings; the scripts never require those paths.

The external test set contains 14 patients, 41 EDF recordings and 47 reference
seizures. Five fixed seeds are analysed: 42, 123, 2026, 27182 and 31415.

## Manuscript values

The authoritative corrected run-level values are stored in
`data/reference/siena_authoritative_runs.csv`. A separate post-hoc reconstruction
from archived scores is labelled as such in every generated output. Minor
differences between the two are expected because one event boundary was corrected
after the original logs were produced; they must not be silently mixed.

## Repository layout

```text
configs/                 locked analysis policy
data/reference/          compact authoritative tables and corrected metadata
data/source_archives/    archived predictions and run logs
docs/                    data access, inference, mapping and limitations
scripts/                 command-line entry points
src/paago_repro/         reusable analysis code
tests/                   deterministic checks
outputs/                 generated; ignored except README
```

## Citation

Use `CITATION.cff`. Please also cite CHB-MIT and Siena Scalp EEG according to
their PhysioNet dataset pages.

## License

Code is released under the MIT License. Derived tables remain subject to the
terms of the source datasets and should not be interpreted as redistributing raw
clinical recordings.

