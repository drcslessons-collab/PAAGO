from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
chb = pd.read_csv(ROOT / "results/chbmit/corrected_metrics_by_seed.csv")
siena = pd.read_csv(ROOT / "results/siena/siena_corrected47_metrics_by_seed.csv")
chb_stats = pd.read_csv(ROOT / "results/statistics/corrected_paired_statistics.csv")
siena_stats = pd.read_csv(ROOT / "results/statistics/siena_corrected47_paired_statistics.csv")
latency = pd.read_csv(ROOT / "results/statistics/conditional_latency_distributions.csv")

assert len(chb) == 45 and len(siena) == 45
assert chb["seed"].nunique() == 5 and siena["seed"].nunique() == 5
assert chb["arm"].nunique() == 9 and siena["arm"].nunique() == 9
assert set(chb["events"].dropna().astype(int)) == {34}
assert set(siena["events"].dropna().astype(int)) == {47}
assert "cohens_dz" in chb_stats.columns and "cohens_dz" in siena_stats.columns
assert len(latency) == 18
assert set(latency["all_reference_seed_events"]) == {170, 235}

print(json.dumps({
    "status": "passed",
    "version": "v1.1.1-neuri-final-revision",
    "chbmit_evaluations": len(chb),
    "siena_evaluations": len(siena),
    "seeds": 5,
    "operating_configurations": 9,
    "chbmit_events": 34,
    "siena_events": 47,
    "paired_effect_size": "Cohen's dz",
}, indent=2))
