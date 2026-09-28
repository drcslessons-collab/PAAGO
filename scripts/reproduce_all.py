from pathlib import Path
import shutil
import sys

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from paago_repro.core import deduplicate_runs, read_csv_members, summarize

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs" / "reproduced"
OUT.mkdir(parents=True, exist_ok=True)

# Recorded per-run results, retained for auditability.
multi = DATA / "source_archives" / "PAAGO_v63_Siena_Multi_Method_Comparison.zip"
f2 = DATA / "source_archives" / "PAAGO_v63_Siena_External_Validation_Results.zip"
frames = read_csv_members(multi, "siena_external_metrics.csv")
frames += read_csv_members(f2, "siena_external_metrics.csv")
runs = deduplicate_runs(frames)
metrics = ["event_sensitivity", "false_alarms_per_hour", "median_latency_sec", "window_roc_auc", "window_pr_auc"]
runs[["method", "seed", *metrics]].to_csv(OUT / "archived_run_metrics.csv", index=False)
summarize(runs, "method", metrics).to_csv(OUT / "archived_metric_summary.csv", index=False)

# Authoritative corrected values used in the paper.
authoritative = pd.read_csv(DATA / "reference" / "siena_authoritative_runs.csv")
authoritative.to_csv(OUT / "siena_authoritative_runs.csv", index=False)
summary = summarize(authoritative, "method", metrics)
summary.to_csv(OUT / "siena_authoritative_summary.csv", index=False)

# Deterministic manuscript-facing plots.
row = summary.loc[summary.method == "PAAGO validation-F2"].iloc[0]
fig, ax = plt.subplots(figsize=(5.6, 4.0))
ax.errorbar([row.event_sensitivity_mean], [row.false_alarms_per_hour_mean],
            xerr=[row.event_sensitivity_sd], yerr=[row.false_alarms_per_hour_sd],
            fmt="o", capsize=4, color="#1769aa")
ax.set(xlabel="Event sensitivity", ylabel="False alarms per hour",
       title="Siena external validation (mean ± SD, five seeds)", xlim=(0, 1))
ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(OUT / "siena_operating_point.png", dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(5.6, 4.0))
ax.bar(["ROC-AUC", "PR-AUC"], [row.window_roc_auc_mean, row.window_pr_auc_mean],
       yerr=[row.window_roc_auc_sd, row.window_pr_auc_sd], capsize=4,
       color=["#1769aa", "#ef6c00"])
ax.set(ylim=(0, 1), ylabel="Score", title="Window-level discrimination on Siena")
ax.grid(axis="y", alpha=.25)
fig.tight_layout(); fig.savefig(OUT / "siena_auc.png", dpi=200); plt.close(fig)

shutil.copy2(DATA / "reference" / "seizure_events.csv", OUT / "seizure_events_corrected47.csv")
print(f"Reproduced tables and figures in {OUT}")

