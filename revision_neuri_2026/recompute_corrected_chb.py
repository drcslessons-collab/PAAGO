from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path("/workspace/scratch/04345731132c")
PRED_DIR = ROOT / "work/final_results/canonical_predictions"
SUPPLIED = ROOT / "paago_required_extracted"
OUT = ROOT / "work/corrected_analysis"
OUT.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 123, 2026, 31415, 27182]
FAMILIES = ["ce", "focal", "adaptive"]


def clean(y, p):
    return np.asarray(y, dtype=int), np.nan_to_num(np.asarray(p, dtype=float), nan=0.0, posinf=1.0, neginf=0.0).clip(0, 1)


def window_metrics(y, p, threshold):
    y, p = clean(y, p)
    pred = (p >= float(threshold)).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "sensitivity": float(recall_score(y, pred, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else np.nan,
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "mcc": float(matthews_corrcoef(y, pred)) if len(np.unique(pred)) > 1 else 0.0,
        "f1": float(f1_score(y, pred, zero_division=0)),
        "f2": float((5 * tp) / (5 * tp + 4 * fn + fp)) if (5 * tp + 4 * fn + fp) else 0.0,
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
    }


def find_threshold(y, p, metric="f1", min_sensitivity=0.0):
    y, p = clean(y, p)
    qs = np.linspace(0.001, 0.999, 199)
    candidates = np.unique(np.concatenate([
        np.linspace(0.001, 0.50, 200),
        np.linspace(0.50, 0.99, 50),
        np.quantile(p, qs),
    ]))
    rows = []
    positives = int(y.sum())
    negatives = int(len(y) - positives)
    # Threshold selection only needs confusion-derived metrics. Avoid recomputing
    # threshold-independent ROC/AP hundreds of times on the 159k validation rows.
    for t in candidates:
        pred = p >= t
        tp = int(np.count_nonzero(pred & (y == 1)))
        fp = int(np.count_nonzero(pred & (y == 0)))
        fn = positives - tp
        tn = negatives - fp
        precision = tp / (tp + fp) if tp + fp else 0.0
        sensitivity = tp / positives if positives else 0.0
        specificity = tn / negatives if negatives else 0.0
        f1 = 2 * precision * sensitivity / (precision + sensitivity) if precision + sensitivity else 0.0
        f2 = 5 * precision * sensitivity / (4 * precision + sensitivity) if 4 * precision + sensitivity else 0.0
        rows.append({"threshold": float(t), "precision": precision, "sensitivity": sensitivity,
                     "specificity": specificity, "f1": f1, "f2": f2})
    feasible = [m for m in rows if m["sensitivity"] >= min_sensitivity]
    pool = feasible or rows
    keyname = "f2" if metric == "f2" else "f1"
    best = max(pool, key=lambda m: (m[keyname], m["f1"], m["specificity"], -m["threshold"]))
    return best["threshold"], best


def corrected_test_labels(test, events):
    y = test.label.to_numpy(dtype=np.int8).copy()
    for e in events.itertuples(index=False):
        mask = (
            test.edf_path.eq(e.edf_path).to_numpy()
            & (test.start_sec.to_numpy(dtype=float) < float(e.end_sec))
            & ((test.start_sec.to_numpy(dtype=float) + 10.0) > float(e.onset_sec))
        )
        y[mask] = 1
    return y


def build_alarms(test, pred, refractory=30.0):
    decisions = test.start_sec.to_numpy(dtype=float) + 10.0
    alarms = []
    for edf in pd.unique(test.edf_path):
        mask = test.edf_path.eq(edf).to_numpy() & pred
        times = np.sort(decisions[mask])
        if len(times) == 0:
            continue
        start = last = float(times[0])
        for t in times[1:]:
            t = float(t)
            if t - last <= refractory:
                last = t
            else:
                alarms.append({"edf_path": edf, "start": start, "end": last, "duration": last - start})
                start = last = t
        alarms.append({"edf_path": edf, "start": start, "end": last, "duration": last - start})
    return alarms, decisions


def event_metrics(test, events, p, threshold, refractory=30.0):
    pred = np.asarray(p) >= threshold
    alarms, decisions = build_alarms(test, pred, refractory)
    matched = set()
    event_rows = []
    for e in events.itertuples(index=False):
        same = test.edf_path.eq(e.edf_path).to_numpy()
        qualifying = same & pred & (decisions >= e.onset_sec) & (decisions <= e.end_sec)
        dts = decisions[qualifying]
        detected = bool(len(dts))
        latency = float(dts.min() - e.onset_sec) if detected else np.nan
        for i, a in enumerate(alarms):
            if a["edf_path"] == e.edf_path and a["start"] <= e.end_sec and a["end"] >= e.onset_sec:
                if detected:
                    matched.add(i)
        event_rows.append({
            "event_id": int(e.event_id), "patient": e.patient, "edf_path": e.edf_path,
            "onset_sec": e.onset_sec, "end_sec": e.end_sec,
            "detected": detected, "latency_sec": latency,
        })
    er = pd.DataFrame(event_rows)
    false_ids = [i for i in range(len(alarms)) if i not in matched]
    false_alarms = len(false_ids)
    interictal_hours_by_patient = {
        "chb20": 27.515556, "chb22": 30.946111, "chb23": 26.437778, "chb24": 21.153889
    }
    total_hours = sum(interictal_hours_by_patient.values())
    lat = er.loc[er.detected, "latency_sec"].to_numpy(dtype=float)
    out = {
        "events": int(len(er)), "detected_events": int(er.detected.sum()),
        "missed_events": int((~er.detected).sum()),
        "event_sensitivity": float(er.detected.mean()),
        "false_alarms": int(false_alarms), "interictal_hours": total_hours,
        "false_alarms_per_hour": float(false_alarms / total_hours),
        "alarm_episodes": int(len(alarms)),
        "median_latency_sec": float(np.median(lat)) if len(lat) else np.nan,
        "mean_latency_sec": float(np.mean(lat)) if len(lat) else np.nan,
        "detected_within_5s_all_events": float(np.mean(er.detected & er.latency_sec.le(5))),
        "detected_within_10s_all_events": float(np.mean(er.detected & er.latency_sec.le(10))),
        "detected_within_30s_all_events": float(np.mean(er.detected & er.latency_sec.le(30))),
        "detected_within_60s_all_events": float(np.mean(er.detected & er.latency_sec.le(60))),
        "conditional_within_30s": float(np.mean(lat <= 30)) if len(lat) else np.nan,
        "mean_alarm_duration_sec": float(np.mean([a["duration"] for a in alarms])) if alarms else 0.0,
        "median_alarm_duration_sec": float(np.median([a["duration"] for a in alarms])) if alarms else 0.0,
        "alarm_time_sec": float(sum(a["duration"] + 5.0 for a in alarms)),
    }
    out["proportion_interictal_time_in_alarm"] = out["alarm_time_sec"] / (total_hours * 3600)

    patient_rows = []
    for patient, hours in interictal_hours_by_patient.items():
        pe = er[er.patient == patient]
        patient_edfs = set(test.loc[test.patient.eq(patient), "edf_path"])
        p_false = sum(1 for i in false_ids if alarms[i]["edf_path"] in patient_edfs)
        p_lat = pe.loc[pe.detected, "latency_sec"].to_numpy(dtype=float)
        patient_rows.append({
            "patient": patient, "events": int(len(pe)), "detected_events": int(pe.detected.sum()),
            "missed_events": int((~pe.detected).sum()), "event_sensitivity": float(pe.detected.mean()),
            "false_alarms": int(p_false), "interictal_hours": hours,
            "false_alarms_per_hour": float(p_false / hours),
            "median_latency_sec": float(np.median(p_lat)) if len(p_lat) else np.nan,
        })
    return out, pd.DataFrame(patient_rows), er


def summarize(df, group="arm"):
    metrics = [
        "threshold", "f1", "f2", "precision", "sensitivity", "specificity", "balanced_accuracy", "mcc",
        "roc_auc", "pr_auc", "event_sensitivity", "false_alarms_per_hour", "median_latency_sec",
        "detected_within_30s_all_events", "mean_alarm_duration_sec", "proportion_interictal_time_in_alarm",
        "equal_patient_event_sensitivity", "equal_patient_false_alarms_per_hour",
    ]
    rows = []
    for name, g in df.groupby(group, sort=False):
        row = {group: name, "n_seeds": len(g)}
        for m in metrics:
            vals = pd.to_numeric(g[m], errors="coerce")
            row[f"{m}_mean"] = vals.mean()
            row[f"{m}_std"] = vals.std(ddof=1)
        rows.append(row)
    return pd.DataFrame(rows)


def paired_stats(df):
    comparisons = [
        ("ce_valf2", "focal_valf2"), ("ce_valf2", "adaptive_valf2"),
        ("focal_valf2", "adaptive_valf2"), ("adaptive_valf1", "adaptive_valf2"),
    ]
    metrics = ["f1", "f2", "event_sensitivity", "false_alarms_per_hour", "roc_auc", "pr_auc"]
    rows = []
    for base, comp in comparisons:
        a = df[df.arm == base].set_index("seed")
        b = df[df.arm == comp].set_index("seed")
        for m in metrics:
            d = (b[m] - a[m]).dropna().to_numpy(dtype=float)
            nonzero = d[~np.isclose(d, 0)]
            if len(nonzero):
                stat, p = wilcoxon(nonzero, alternative="two-sided", method="exact")
            else:
                stat, p = np.nan, np.nan
            dz = float(d.mean() / d.std(ddof=1)) if len(d) > 1 and d.std(ddof=1) > 0 else np.nan
            rows.append({"baseline": base, "comparison": comp, "metric": m, "n_pairs": len(d),
                         "nonzero_pairs": len(nonzero), "mean_delta": d.mean(), "cohens_dz": dz,
                         "wilcoxon_statistic": stat, "p_value_two_sided_raw": p})
    out = pd.DataFrame(rows)
    # Holm correction within the prespecified matched-F2 family for each metric (3 comparisons).
    out["p_holm_within_metric"] = np.nan
    for m, idx in out.groupby("metric").groups.items():
        ids = list(idx)[:3]
        valid = [(i, out.loc[i, "p_value_two_sided_raw"]) for i in ids if pd.notna(out.loc[i, "p_value_two_sided_raw"])]
        valid.sort(key=lambda x: x[1])
        adj = {}
        running = 0.0
        n = len(valid)
        for rank, (i, p) in enumerate(valid):
            running = max(running, min(1.0, (n-rank)*p))
            adj[i] = running
        for i, v in adj.items(): out.loc[i, "p_holm_within_metric"] = v
    return out


def main():
    manifest = pd.read_csv(SUPPLIED / "manifest/manifest_patient_v63_validation_test.csv.gz", low_memory=False)
    val = manifest[manifest.split.str.lower().eq("val")].reset_index(drop=True)
    test = manifest[manifest.split.str.lower().eq("test")].reset_index(drop=True)
    events = pd.read_csv(SUPPLIED / "event_detection/reference_seizure_events.csv")
    y_test_corrected = corrected_test_labels(test, events)
    assert int(y_test_corrected.sum()) == 344
    all_rows, patient_frames, event_frames, sensitivity_rows = [], [], [], []
    policies = [("fixed05", "fixed", 0.0), ("valf1", "f1", 0.0), ("valf2", "f2", 0.55)]
    for family in FAMILIES:
        for seed in SEEDS:
            dat = np.load(PRED_DIR / f"{family}_seed{seed}.npz")
            y_val, p_val, p_test = dat["y_val"], dat["p_val"], dat["p_test"]
            assert np.array_equal(y_val, val.label.to_numpy(dtype=np.int8))
            for suffix, metric, min_sens in policies:
                if metric == "fixed": threshold = 0.5
                else: threshold, _ = find_threshold(y_val, p_val, metric=metric, min_sensitivity=min_sens)
                arm = f"{family}_{suffix}"
                wm = window_metrics(y_test_corrected, p_test, threshold)
                em, pm, ed = event_metrics(test, events, p_test, threshold, refractory=30.0)
                row = {"arm": arm, "family": family, "policy": suffix, "seed": seed, **wm, **em}
                row["equal_patient_event_sensitivity"] = pm.event_sensitivity.mean()
                row["equal_patient_false_alarms_per_hour"] = pm.false_alarms_per_hour.mean()
                all_rows.append(row)
                pm.insert(0, "seed", seed); pm.insert(0, "arm", arm); patient_frames.append(pm)
                ed.insert(0, "seed", seed); ed.insert(0, "arm", arm); event_frames.append(ed)
                if suffix == "valf2":
                    for ref in [0, 10, 20, 30, 60]:
                        em2, _, _ = event_metrics(test, events, p_test, threshold, refractory=float(ref))
                        sensitivity_rows.append({"arm": arm, "seed": seed, "refractory_sec": ref,
                                                 "event_sensitivity": em2["event_sensitivity"],
                                                 "false_alarms_per_hour": em2["false_alarms_per_hour"],
                                                 "alarm_episodes": em2["alarm_episodes"]})
    runs = pd.DataFrame(all_rows)
    patients = pd.concat(patient_frames, ignore_index=True)
    details = pd.concat(event_frames, ignore_index=True)
    runs.to_csv(OUT / "corrected_metrics_by_seed.csv", index=False)
    summarize(runs).to_csv(OUT / "corrected_metrics_summary.csv", index=False)
    patients.to_csv(OUT / "corrected_patient_metrics_all_runs.csv", index=False)
    details.to_csv(OUT / "corrected_event_details_all_runs.csv", index=False)
    pd.DataFrame(sensitivity_rows).to_csv(OUT / "refractory_sensitivity_analysis.csv", index=False)
    paired_stats(runs).to_csv(OUT / "corrected_paired_statistics.csv", index=False)
    audit = {
        "test_rows": len(test), "positive_windows_original": int(test.label.sum()),
        "positive_windows_corrected": int(y_test_corrected.sum()), "reference_events": len(events),
        "test_patients": sorted(test.patient.unique().tolist()),
        "policies": {"fixed05": "0.5", "valf1": "validation F1", "valf2": "validation F2 with minimum sensitivity 0.55"},
        "shared_prediction_families": FAMILIES, "seeds": SEEDS,
        "event_decision_time": "window end (start+10 s)", "event_detection_rule": "decision time in [onset, offset]",
        "alarm_merge_rule": "same-EDF positive decisions with successive gaps <= refractory period",
        "default_refractory_sec": 30,
    }
    (OUT / "corrected_analysis_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(summarize(runs).to_string(index=False))


if __name__ == "__main__":
    main()
