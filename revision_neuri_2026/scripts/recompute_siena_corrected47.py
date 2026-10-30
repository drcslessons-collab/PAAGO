from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, confusion_matrix,
    f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score,
)

ROOT = Path("/workspace/scratch/04345731132c")
SIENA = ROOT / "work/siena_multi"
EVENTS_CSV = ROOT / "work/siena_event_metadata/persistent_siena_cache_corrected47__seizure_events.csv"
CHB_RUNS = ROOT / "work/corrected_analysis/corrected_metrics_by_seed.csv"
OUT = ROOT / "work/siena_corrected47_analysis"
OUT.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 123, 2026, 31415, 27182]
FAMILIES = ["ce", "focal", "adaptive"]


def basename_series(values):
    return values.astype(str).str.replace("\\", "/", regex=False).str.rsplit("/", n=1).str[-1]


def prediction_files():
    found = {}
    roots = {
        "ce": SIENA / "CE_validation_F1",
        "focal": SIENA / "Fixed_Focal_validation_F1",
        "adaptive": SIENA / "PAAGO_validation_F1",
    }
    for family, root in roots.items():
        files = sorted(root.rglob("siena_predictions.csv"))
        for seed in SEEDS:
            matches = [p for p in files if re.search(rf"seed{seed}(?:/|$)", str(p).replace("_", ""))]
            # Prefer top-level CE corrected copies, but labels are rebuilt in all cases.
            if family == "ce":
                top = [p for p in matches if "/seed_" not in str(p)]
                matches = top or matches
            else:
                nested = [p for p in matches if f"/seed_{seed}/" in str(p)]
                matches = nested or matches
            if not matches:
                raise FileNotFoundError(f"No predictions for {family}, seed {seed}")
            found[(family, seed)] = matches[0]
    return found


def rebuild_labels(rows, events):
    starts = rows.start_sec.to_numpy(float)
    edfs = basename_series(rows.edf_path).to_numpy()
    y = np.zeros(len(rows), dtype=np.int8)
    for e in events.itertuples(index=False):
        mask = (edfs == e.edf_file) & (starts < e.offset_sec) & ((starts + 10.0) > e.onset_sec)
        y[mask] = 1
    return y


def window_metrics(y, p, threshold):
    p = np.nan_to_num(np.asarray(p, float), nan=0, posinf=1, neginf=0).clip(0, 1)
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "precision": precision_score(y, pred, zero_division=0),
        "sensitivity": recall_score(y, pred, zero_division=0),
        "specificity": tn / (tn + fp),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "mcc": matthews_corrcoef(y, pred) if len(np.unique(pred)) > 1 else 0.0,
        "f1": f1_score(y, pred, zero_division=0),
        "f2": (5 * tp) / (5 * tp + 4 * fn + fp) if 5 * tp + 4 * fn + fp else 0.0,
        "roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
    }


def build_alarms(rows, pred, refractory=30.0):
    decisions = rows.start_sec.to_numpy(float) + 10.0
    edfs = basename_series(rows.edf_path).to_numpy()
    alarms = []
    for edf in pd.unique(edfs):
        times = np.sort(decisions[(edfs == edf) & pred])
        if not len(times):
            continue
        first = last = float(times[0])
        for t in times[1:]:
            t = float(t)
            if t - last <= refractory:
                last = t
            else:
                alarms.append({"edf_file": edf, "start": first, "end": last})
                first = last = t
        alarms.append({"edf_file": edf, "start": first, "end": last})
    return alarms, decisions, edfs


def event_metrics(rows, events, p, threshold, interictal_hours, patient_hours, refractory=30.0):
    pred = np.asarray(p, float) >= threshold
    alarms, decisions, edfs = build_alarms(rows, pred, refractory)
    matched = set()
    event_rows = []
    for event_id, e in enumerate(events.itertuples(index=False), start=1):
        q = (edfs == e.edf_file) & pred & (decisions >= e.onset_sec) & (decisions <= e.offset_sec)
        dts = decisions[q]
        detected = bool(len(dts))
        latency = float(dts.min() - e.onset_sec) if detected else np.nan
        if detected:
            for i, a in enumerate(alarms):
                if a["edf_file"] == e.edf_file and a["start"] <= e.offset_sec and a["end"] >= e.onset_sec:
                    matched.add(i)
        event_rows.append({"event_id": event_id, "patient": e.patient, "edf_file": e.edf_file,
                           "onset_sec": e.onset_sec, "offset_sec": e.offset_sec,
                           "detected": detected, "latency_sec": latency})
    er = pd.DataFrame(event_rows)
    false_ids = [i for i in range(len(alarms)) if i not in matched]
    lat = er.loc[er.detected, "latency_sec"].to_numpy(float)
    summary = {
        "events": len(er), "detected_events": int(er.detected.sum()),
        "event_sensitivity": er.detected.mean(), "false_alarms": len(false_ids),
        "interictal_hours": interictal_hours,
        "false_alarms_per_hour": len(false_ids) / interictal_hours,
        "alarm_episodes": len(alarms),
        "median_latency_sec": np.median(lat) if len(lat) else np.nan,
        "mean_latency_sec": np.mean(lat) if len(lat) else np.nan,
        "detected_within_30s_all_events": np.mean(er.detected & er.latency_sec.le(30)),
    }
    patient_rows = []
    for patient in sorted(events.patient.unique()):
        pe = er[er.patient == patient]
        patient_edfs = set(events.loc[events.patient == patient, "edf_file"])
        pf = sum(1 for i in false_ids if alarms[i]["edf_file"] in patient_edfs)
        plat = pe.loc[pe.detected, "latency_sec"].to_numpy(float)
        ph = patient_hours[patient]
        patient_rows.append({"patient": patient, "events": len(pe), "detected_events": int(pe.detected.sum()),
                             "event_sensitivity": pe.detected.mean(), "false_alarms": pf,
                             "interictal_hours": ph, "false_alarms_per_hour": pf / ph,
                             "median_latency_sec": np.median(plat) if len(plat) else np.nan})
    return summary, pd.DataFrame(patient_rows), er


def summarize(runs):
    metrics = ["threshold", "f1", "f2", "precision", "sensitivity", "specificity", "mcc", "roc_auc", "pr_auc",
               "event_sensitivity", "false_alarms_per_hour", "median_latency_sec",
               "equal_patient_event_sensitivity", "equal_patient_false_alarms_per_hour"]
    out = []
    for arm, g in runs.groupby("arm", sort=False):
        row = {"arm": arm, "n_seeds": len(g)}
        for m in metrics:
            row[f"{m}_mean"] = g[m].mean()
            row[f"{m}_std"] = g[m].std(ddof=1)
        out.append(row)
    return pd.DataFrame(out)


def paired_stats(runs):
    comparisons = [("ce_valf2", "focal_valf2"), ("ce_valf2", "adaptive_valf2"), ("focal_valf2", "adaptive_valf2")]
    metrics = ["f1", "f2", "event_sensitivity", "false_alarms_per_hour", "roc_auc", "pr_auc"]
    rows = []
    for a, b in comparisons:
        aa, bb = runs[runs.arm == a].set_index("seed"), runs[runs.arm == b].set_index("seed")
        for m in metrics:
            delta = (bb[m] - aa[m]).to_numpy(float)
            nz = delta[~np.isclose(delta, 0)]
            stat, p = wilcoxon(nz, method="exact") if len(nz) else (np.nan, np.nan)
            rows.append({"baseline": a, "comparison": b, "metric": m, "n_pairs": len(delta),
                         "mean_delta": delta.mean(), "wilcoxon_statistic": stat, "p_value_raw": p})
    out = pd.DataFrame(rows)
    out["p_holm_within_metric"] = np.nan
    for metric, idx in out.groupby("metric").groups.items():
        ordered = sorted([(i, out.loc[i, "p_value_raw"]) for i in idx], key=lambda z: z[1])
        running = 0.0
        for rank, (i, p) in enumerate(ordered):
            running = max(running, min(1.0, (len(ordered)-rank)*p))
            out.loc[i, "p_holm_within_metric"] = running
    return out


def main():
    events = pd.read_csv(EVENTS_CSV)
    events["edf_file"] = basename_series(events.edf_path)
    assert len(events) == 47
    # The corrected47 export retained clock-of-day seconds for the second
    # PN12-1.2 event. Convert 18:31:01--18:32:09 relative to the recording
    # start 15:51:31, yielding 9570--9638 s within the EDF.
    pn12_clock = (events.edf_file == "PN12-1.2.edf") & (events.onset_sec == 66661.0)
    assert int(pn12_clock.sum()) == 1
    events.loc[pn12_clock, ["onset_sec", "offset_sec"]] = [9570.0, 9638.0]
    chb = pd.read_csv(CHB_RUNS)
    files = prediction_files()
    reference = pd.read_csv(files[("ce", 42)])
    y = rebuild_labels(reference, events)
    # 47-event authoritative reconstruction, including the second PN12-1.2 event.
    assert int(y.sum()) == 984, int(y.sum())
    durations = reference.groupby(basename_series(reference.edf_path)).start_sec.max() + 10.0
    ictal_by_edf = events.assign(duration=events.offset_sec-events.onset_sec).groupby("edf_file").duration.sum()
    interictal_hours = (durations.sum() - ictal_by_edf.sum()) / 3600
    patient_by_edf = reference.assign(edf_file=basename_series(reference.edf_path)).drop_duplicates("edf_file").set_index("edf_file").patient
    patient_hours = {}
    for patient in sorted(events.patient.unique()):
        patient_edfs = patient_by_edf[patient_by_edf == patient].index
        patient_hours[patient] = (durations.reindex(patient_edfs).sum() - ictal_by_edf.reindex(patient_edfs).fillna(0).sum()) / 3600
    rows, patient_frames, event_frames = [], [], []
    for family in FAMILIES:
        for seed in SEEDS:
            dat = pd.read_csv(files[(family, seed)])
            assert np.array_equal(basename_series(dat.edf_path).to_numpy(), basename_series(reference.edf_path).to_numpy())
            assert np.array_equal(dat.start_sec.to_numpy(), reference.start_sec.to_numpy())
            p = dat.probability.to_numpy(float)
            for policy in ["fixed05", "valf1", "valf2"]:
                arm = f"{family}_{policy}"
                threshold = 0.5 if policy == "fixed05" else float(chb.loc[(chb.family == family) & (chb.seed == seed) & (chb.policy == policy), "threshold"].iloc[0])
                wm = window_metrics(y, p, threshold)
                em, pm, er = event_metrics(reference, events, p, threshold, interictal_hours, patient_hours)
                row = {"arm": arm, "family": family, "policy": policy, "seed": seed, **wm, **em}
                row["equal_patient_event_sensitivity"] = pm.event_sensitivity.mean()
                row["equal_patient_false_alarms_per_hour"] = pm.false_alarms_per_hour.mean()
                rows.append(row)
                pm.insert(0, "seed", seed); pm.insert(0, "arm", arm); patient_frames.append(pm)
                er.insert(0, "seed", seed); er.insert(0, "arm", arm); event_frames.append(er)
    runs = pd.DataFrame(rows)
    runs.to_csv(OUT / "siena_corrected47_metrics_by_seed.csv", index=False)
    summarize(runs).to_csv(OUT / "siena_corrected47_metrics_summary.csv", index=False)
    pd.concat(patient_frames).to_csv(OUT / "siena_corrected47_patient_metrics.csv", index=False)
    pd.concat(event_frames).to_csv(OUT / "siena_corrected47_event_details.csv", index=False)
    paired_stats(runs).to_csv(OUT / "siena_corrected47_paired_statistics.csv", index=False)
    audit = {"windows": len(reference), "ictal_windows": int(y.sum()), "patients": int(events.patient.nunique()),
             "edf_files": int(reference.edf_path.nunique()), "reference_events": len(events),
             "recording_hours": durations.sum()/3600, "ictal_hours": ictal_by_edf.sum()/3600,
             "interictal_hours": interictal_hours, "window_sec": 10.0, "stride_sec": 5.0,
             "decision_time": "window end", "alarm_refractory_sec": 30.0,
             "threshold_source": "CHB-MIT validation scores; frozen for Siena",
             "annotation_correction": {
                 "edf_file": "PN12-1.2.edf", "event": 2,
                 "exported_clock_seconds": [66661.0, 66729.0],
                 "recording_start_clock": "15:51:31",
                 "event_clock": ["18:31:01", "18:32:09"],
                 "corrected_elapsed_seconds": [9570.0, 9638.0]
             }}
    (OUT / "siena_corrected47_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(summarize(runs).to_string(index=False))
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
