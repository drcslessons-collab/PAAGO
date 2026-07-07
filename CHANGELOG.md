# Changelog

## v2.1 GitHub Edition

- Prepared lightweight GitHub-ready repository.
- Removed full `runs/` artifacts and checkpoint files from the tracked package.
- Added stronger `.gitignore` rules for checkpoints, raw EEG data, caches, archives, and logs.
- Added `docs/RELEASE_ASSETS.md` to document how to host large artifacts externally.
- Kept source code, configs, tests, documentation, and lightweight CSV result summaries.


## v2.0 - 2026-07-07

- Integrated complete supplied PAAGO model source code under `models/`.
- Added `models.__init__` exports for `EEGFPN` and core components.
- Added architecture documentation in `docs/MODEL_ARCHITECTURE.md`.
- Added runnable model forward-pass example in `examples/model_forward_example.py`.
- Added model shape test in `tests/test_model_forward.py`.
- Updated package metadata to version 2.0.0 and included the `models` package.
- Removed generated Python cache folders from the publication package.


## v1.0.0 - 2026-07-07

- Initial PAAGO publication repository package.
- Added v62 configurations for five experiments and three seeds.
- Added training engine, utility scripts, patient audit outputs, result tables, figures, and checkpoints from uploaded artifacts.
- Added repository metadata: README, LICENSE, CITATION.cff, requirements, environment, documentation, examples, and lightweight tests.
