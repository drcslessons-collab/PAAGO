# Annotation corrections

## CHB-MIT

The corrected event audit recovered 16 seizures in chb24. The corrected test labels contain 344 ictal windows and 34 seizure events.

## Siena

The second event in PN12-1.2.edf was converted from clock time 18:31:01-18:32:09 relative to recording start 15:51:31, giving elapsed time 9,570-9,638 s. The corrected evaluation contains 47 seizure events and 984 ictal windows.

## Scope

Canonical checkpoints, stored continuous scores, validation checkpoint selection, and validation-selected thresholds were fixed before these corrections. The corrections changed evaluation labels and scoring only. No model was retrained, no checkpoint was reselected, and no threshold or hyperparameter was adjusted using corrected test outcomes.
