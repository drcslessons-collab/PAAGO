from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv_members(archive: Path, suffix: str) -> list[pd.DataFrame]:
    frames = []
    with zipfile.ZipFile(archive) as zf:
        names = sorted(n for n in zf.namelist() if n.endswith(suffix))
        for name in names:
            with zf.open(name) as stream:
                frame = pd.read_csv(stream)
                frame.insert(0, "archive_member", name)
                frames.append(frame)
    return frames


def summarize(df: pd.DataFrame, group: str, metrics: list[str]) -> pd.DataFrame:
    out = []
    for key, part in df.groupby(group, sort=True):
        row = {group: key, "n_runs": len(part)}
        for metric in metrics:
            values = pd.to_numeric(part[metric], errors="coerce")
            row[f"{metric}_mean"] = values.mean()
            row[f"{metric}_sd"] = values.std(ddof=1)
        out.append(row)
    return pd.DataFrame(out)


def load_config(root: Path) -> dict:
    return json.loads((root / "configs" / "analysis.json").read_text())


def parse_seed(text: str) -> int:
    import re
    match = re.search(r"seed[_-]?(\d+)", text, re.I)
    if not match:
        raise ValueError(f"No seed in {text}")
    return int(match.group(1))


def method_from_member(name: str) -> str:
    if "CE_validation" in name or "exp2_ce" in name:
        return "CE validation-F1"
    if "Fixed_Focal" in name or "exp4_focal" in name:
        return "Focal validation-F1"
    if "PAAGO_validation" in name or "exp6_paago" in name:
        return "PAAGO validation-F1"
    if "exp7_paago" in name:
        return "PAAGO validation-F2"
    return "unknown"


def deduplicate_runs(frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for frame in frames:
        row = frame.iloc[0].copy()
        member = str(row["archive_member"])
        row["seed"] = parse_seed(member)
        row["method"] = method_from_member(member)
        rows.append(row)
    df = pd.DataFrame(rows)
    # Archives may contain both consolidated and later per-seed copies.
    return df.sort_values("archive_member").drop_duplicates(["method", "seed"], keep="last")


def paired_signflip_exact(a: np.ndarray, b: np.ndarray) -> float:
    """Exact two-sided paired sign-flip test for small n (zero differences kept)."""
    d = np.asarray(a, float) - np.asarray(b, float)
    observed = abs(d.mean())
    stats = []
    for mask in range(1 << len(d)):
        signs = np.array([1 if mask & (1 << i) else -1 for i in range(len(d))])
        stats.append(abs((d * signs).mean()))
    return float(np.mean(np.asarray(stats) >= observed - 1e-15))

