"""Generate the paper benchmark table and figure from verified summary JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "experiments/processed_results/reference_benchmark_summary.json"
summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

methods = ["no_response", "reactive", "coordinated"]
labels = ["No response", "Reactive", "Coordinated"]
means = [summary["methods"][method]["affected_area"]["mean"] for method in methods]
stds = [summary["methods"][method]["affected_area"]["std"] for method in methods]

fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.bar(labels, means, yerr=stds, capsize=5)
ax.set_ylabel("Affected cells (mean +/- SD)")
ax.set_title("Reference benchmark: 160 matched scenario-seed cases")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
for suffix in ("pdf", "png"):
    destination = ROOT / f"experiments/figures/reference_benchmark.{suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=300)
plt.close(fig)

rows = []
for method in methods:
    affected = summary["methods"][method]["affected_area"]
    rows.append(
        {
            "method": method,
            "n": affected["n"],
            "affected_mean": affected["mean"],
            "affected_std": affected["std"],
            "affected_median": affected["median"],
            "affected_q25": affected["q25"],
            "affected_q75": affected["q75"],
        }
    )

table_path = ROOT / "experiments/tables/reference_benchmark_summary.csv"
table_path.parent.mkdir(parents=True, exist_ok=True)
with table_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

# Keep paper copies synchronized mechanically.
for relative in (
    "paper/figures/reference_benchmark.pdf",
    "paper/figures/reference_benchmark.png",
):
    destination = ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments" / "figures" / f"reference_benchmark{destination.suffix}"
    destination.write_bytes(source.read_bytes())
(ROOT / "paper/tables/reference_benchmark_summary.csv").write_bytes(table_path.read_bytes())
