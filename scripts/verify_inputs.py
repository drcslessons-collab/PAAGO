from pathlib import Path
import json
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from paago_repro.core import sha256

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ROOT / "data" / "source_archives"
required = {
    "PAAGO_v63_Siena_Multi_Method_Comparison.zip": "siena_external_metrics.csv",
    "PAAGO_v63_Siena_External_Validation_Results.zip": "siena_predictions.csv",
    "Siena_Corrected47_Metadata.zip": "seizure_events.csv",
}

manifest = []
for filename, member_suffix in required.items():
    path = ARCHIVES / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"Corrupt ZIP member: {bad}")
        if not any(n.endswith(member_suffix) for n in zf.namelist()):
            raise RuntimeError(f"{filename} lacks {member_suffix}")
    manifest.append({"file": filename, "bytes": path.stat().st_size, "sha256": sha256(path)})

with zipfile.ZipFile(ARCHIVES / "Siena_Corrected47_Metadata.zip") as zf:
    meta = json.loads(zf.read("metadata.json"))
expected = {"patients": 14, "seizures": 47}
for key, value in expected.items():
    if meta.get(key) != value:
        raise AssertionError(f"metadata {key}={meta.get(key)}; expected {value}")
if len(meta.get("source_sampling_rates", {})) != 41:
    raise AssertionError("Expected 41 EDF entries")

out = ROOT / "outputs" / "reproduced"
out.mkdir(parents=True, exist_ok=True)
(out / "input_manifest.json").write_text(json.dumps({"archives": manifest, "metadata": meta}, indent=2))
print("PASS: archives readable; 14 patients, 41 EDFs, 47 seizures.")

