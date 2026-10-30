from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
chb = pd.read_csv(ROOT / "results/chbmit/corrected_metrics_by_seed.csv")
siena = pd.read_csv(ROOT / "results/siena/siena_corrected47_metrics_by_seed.csv")

assert len(chb) == 45, f"Expected 45 CHB-MIT evaluations, found {len(chb)}"
assert len(siena) == 45, f"Expected 45 Siena evaluations, found {len(siena)}"
assert chb["seed"].nunique() == 5
assert siena["seed"].nunique() == 5
assert chb["arm"].nunique() == 9
assert siena["arm"].nunique() == 9
assert set(chb["events"].dropna().astype(int)) == {34}
assert set(siena["events"].dropna().astype(int)) == {47}

print(json.dumps({
    "status": "passed",
    "chbmit_evaluations": len(chb),
    "siena_evaluations": len(siena),
    "seeds": 5,
    "operating_configurations": 9,
    "chbmit_events": 34,
    "siena_events": 47,
}, indent=2))
