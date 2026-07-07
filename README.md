# PAAGO Publication Repository v2.1 GitHub Edition

Official publication repository for **PAAGO: Prompt-Aware Adaptive Graph Optimization for EEG Seizure Prediction**.

This v2.1 GitHub Edition is a lightweight publication repository prepared for direct upload to GitHub. It includes the complete supplied model source code, experiment configurations, training/evaluation utilities, patient-split audit summaries, ablation summary CSV files, and lightweight tests. Large checkpoint files and per-run artifacts were intentionally removed to keep the repository suitable for GitHub.

## Repository status

**Version:** v2.1 GitHub Edition  
**Model source:** included under `models/`  
**Primary model class:** `models.EEGFPN`  
**Dataset redistribution:** raw EEG data is not included; users must download CHB-MIT from PhysioNet.

## Repository contents

```text
PAAGO_Publication_Repository_v2.0/
├── configs/        # YAML files for CPU/GPU/A100 and five PAAGO ablation experiments
├── models/         # PAAGO model implementation: EEGFPN and core neural components
├── scripts/        # Utility scripts: split audit, threshold calibration, stats collection
├── trainer/        # Training epoch engine and stable focal-loss implementation
├── evaluation/     # Metric utilities for repository completeness
├── outputs/        # Lightweight patient audit reports and v62 ablation summary tables
├── release_assets/ # Instructions for external large artifacts; checkpoints are not included
├── data/           # Dataset instructions; no raw EEG data is redistributed
├── docs/           # Reproducibility notes, architecture notes, and documentation
├── examples/       # Minimal runnable examples
├── paper/          # Citation/BibTeX placeholders and paper notes
└── tests/          # Lightweight repository tests
```

## Model architecture

PAAGO is implemented as `EEGFPN`, combining:

1. adaptive multi-kernel temporal EEG encoding,
2. dynamic graph learning over EEG channels,
3. cross-attention temporal–graph fusion,
4. transformer-based channel-context modeling,
5. attention pooling,
6. classification and continuous risk-score heads.

See `docs/MODEL_ARCHITECTURE.md` for the technical description and minimal inference example.


## Large artifacts

The full `runs/` directory and model checkpoints (`*.pt`, `*.pth`, `*.ckpt`) are not included in this GitHub Edition. Store those files externally using Zenodo, GitHub Releases, institutional storage, or Google Drive, then add the final DOI/link here and in `docs/RELEASE_ASSETS.md`.

## Main v62 ablation results

The summary file is available at `outputs/v62_ablation_summary.csv`.

| Experiment | Seeds | F1 mean ± std | Sensitivity mean ± std | Specificity mean ± std | ROC-AUC mean ± std |
|---|---:|---:|---:|---:|---:|
| exp1_ce_baseline | 3 | 0.2778 ± 0.2119 | 0.7735 ± 0.0948 | 0.7644 ± 0.2257 | 0.8756 ± 0.0672 |
| exp2_focal_fixed | 3 | 0.5130 ± 0.1922 | 0.6336 ± 0.2238 | 0.9524 ± 0.0746 | 0.9388 ± 0.0058 |
| exp3_adaptive_gamma | 3 | 0.5671 ± 0.1388 | 0.6908 ± 0.1719 | 0.9668 ± 0.0434 | 0.9439 ± 0.0034 |
| exp4_adaptive_gamma_ema | 3 | 0.3006 ± 0.1141 | 0.3193 ± 0.2721 | 0.9791 ± 0.0325 | 0.9064 ± 0.0309 |
| exp5_full_sensitivity | 3 | 0.4406 ± 0.1116 | 0.5229 ± 0.1633 | 0.9619 ± 0.0499 | 0.9064 ± 0.0309 |

In this artifact set, `exp3_adaptive_gamma` gives the highest mean F1 and ROC-AUC, while `exp1_ce_baseline` gives the highest mean sensitivity.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For a Conda environment:

```bash
conda env create -f environment.yml
conda activate paago
```

Optional editable install:

```bash
pip install -e .
```

## Minimal model check

```bash
python examples/model_forward_example.py
```

Expected output:

```text
logits: (2, 2)
risk: (2,)
adjacency: (2, 21, 21)
node_attention: (2, 21)
```

## Dataset

Raw CHB-MIT EEG recordings are not redistributed in this repository. Download the dataset from PhysioNet and build the cached dataset expected by the configs:

```text
data/EEG_FPN_Cache_v4/
├── manifest_patient.csv
├── train/
├── val/
└── test/
```

See `data/README.md` and `data/dataset_links.md`.

## Reproducing the five experiments

After preparing the cache and confirming the training entry point in your local environment, run the seed-specific configuration files. The v62 experiment configs are included for seeds `42`, `123`, and `2026`:

```bash
python train.py --config configs/v62_exp1_ce_baseline_seed42.yaml
python train.py --config configs/v62_exp2_focal_fixed_seed42.yaml
python train.py --config configs/v62_exp3_adaptive_gamma_seed42.yaml
python train.py --config configs/v62_exp4_adaptive_gamma_ema_seed42.yaml
python train.py --config configs/v62_exp5_full_sensitivity_seed42.yaml
```

Run the corresponding files for seeds `123` and `2026` to reproduce the full v62 table.

## Result aggregation

```bash
python scripts/collect_v62_stats.py
```

Outputs:

```text
outputs/v62_best_runs.csv
outputs/v62_ablation_summary.csv
outputs/v62_ablation_stats.csv
```

## Patient split audit

```bash
python scripts/audit_patient_split.py --manifest data/EEG_FPN_Cache_v4/manifest_patient.csv
```

Existing audit outputs are included under:

```text
outputs/v61_patient_audit_manifest_patient/
outputs/v61_patient_audit_original/
```

## Testing

```bash
PYTHONPATH=. pytest -q tests/test_metrics.py tests/test_repository_artifacts.py tests/test_model_forward.py
```

Repository health check on this package: **3 tests passed**.

## Citation

Use `CITATION.cff` or the BibTeX template in `paper/PAAGO.bib` after the manuscript metadata is finalized.

## License

This repository is distributed under the MIT License unless a journal, dataset provider, or institutional policy requires a different license.
