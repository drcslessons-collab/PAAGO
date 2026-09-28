# Data dictionary

## `reference/siena_authoritative_runs.csv`

Corrected manuscript-facing run-level metrics. `locked_threshold` was selected
without access to Siena labels. `event_sensitivity` is detected reference events
divided by all reference events. `false_alarms_per_hour` uses interictal hours.
Latency is seconds from reference onset to the first overlapping alarm.

## `reference/seizure_events.csv`

Corrected 47-event inventory. Times are seconds relative to each EDF recording.

## `source_archives/*.zip`

Immutable evidence supplied by the author: window scores, run metrics and the
corrected metadata. `verify_inputs.py` records SHA-256 hashes for provenance.

Raw EEG and checkpoints are not included.

