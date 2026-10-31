# Cohort and retained-provenance limitations

- The canonical patient sets are mutually disjoint after normalizing `chb21` to `chb01`.
- The source release contains 24 case directories. `chb12` is absent from the retained canonical manifest, but the archived reviewer export does not preserve a machine-verifiable exclusion log; no retrospective reason is asserted.
- The retained export contains 470,926 training, 159,517 validation, and 76,554 test windows.
- Validation class counts retained in the export are 376 ictal and 159,141 nonictal windows.
- Corrected held-out test counts are 344 ictal and 76,210 nonictal windows, 34 seizures, and 106.05 interictal hours.
- Historical train/validation seizure totals, exposure totals, and the complete train/validation annotation audit are not retained and are represented as unavailable rather than reconstructed.
- Exact selected epochs are not retained in the exported training histories. Family, seed, frozen threshold, and checkpoint SHA-256 identifiers provide the available checkpoint provenance.
- Siena time-in-alarm was not retained in the archived external score export and is not reconstructed.
