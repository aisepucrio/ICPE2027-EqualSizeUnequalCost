"""Merge per-part FSE-posterior outputs into one family directory, as a monolithic batch run would write it.

Parts are concatenated in the monolithic loop order (raw CSV strings are kept, so values are
byte-identical to what each part wrote); budget trends and the family report are recomputed with
the repository's own functions.

Usage: python merge_parts.py <repo_root> <parts_root> <out_root> <family> [--allow-partial]
family: energy | workload | lcbench
"""
import csv
import sys
from pathlib import Path

import pandas as pd

REPO, PARTS, OUT, FAMILY = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
ALLOW_PARTIAL = "--allow-partial" in sys.argv
sys.path[:0] = [str(REPO), str(REPO / "scripts")]
from cost_sampling.analysis import level_sort_key, write_csv  # noqa: E402

COMMON = ["posterior_records.csv", "posterior_strategy_summary.csv", "posterior_confidence_curves.csv",
          "posterior_pareto.csv", "posterior_hypothesis_tests.csv", "posterior_hypothesis_summary.csv"]

if FAMILY == "energy":
    from run_fse_posterior_twins_batch import ALL_SYSTEMS
    from fse_posterior_generated_common import strategy_budget_trends, write_family_report
    out_dir, scope_csv, scope_key = "fse_posterior_energy_final", "posterior_energy_scenario_summary.csv", "scenario"
    trend_csv, report = "posterior_energy_budget_trends.csv", "fse_posterior_energy_report.md"
    props = ["energy", "performance"]

    def order(part):
        s, c, t = part.name.split("__")
        return (ALL_SYSTEMS.index(s), props.index(c), props.index(t))
    expected = len(ALL_SYSTEMS) * 4
elif FAMILY == "workload":
    from run_fse_posterior_workload_batch import ALL_SYSTEMS
    from fse_posterior_generated_common import strategy_budget_trends, write_family_report
    out_dir, scope_csv, scope_key = "fse_posterior_workload_final", "posterior_workload_context_summary.csv", "context_pair"
    trend_csv, report = "posterior_workload_budget_trends.csv", "fse_posterior_workload_report.md"

    def order(part):
        first = next(csv.DictReader(open(part / scope_csv, newline="")))
        system, workload = first["context_pair"].split("__", 1)
        return (ALL_SYSTEMS.index(system), workload)
    expected = 93
elif FAMILY == "lcbench":
    from run_fse_posterior_lcbench_batch import strategy_budget_trends, write_batch_report
    out_dir, scope_csv, scope_key = "fse_posterior_lcbench_no_oracles_final", "posterior_lcbench_dataset_summary.csv", "workload"
    trend_csv, report = "posterior_lcbench_budget_trends.csv", "fse_posterior_lcbench_report.md"

    def order(part):
        return next(csv.DictReader(open(part / scope_csv, newline="")))["workload"]
    expected = 35
else:
    raise SystemExit(f"unknown family {FAMILY}")

parts = [p for p in (PARTS / FAMILY).iterdir() if (p / scope_csv).exists() and (p / scope_csv).stat().st_size > 0]
print(f"[merge {FAMILY}] {len(parts)}/{expected} complete parts")
if len(parts) != expected and not ALLOW_PARTIAL:
    raise SystemExit("incomplete; not merging")
parts.sort(key=order)
target = OUT / out_dir
target.mkdir(parents=True, exist_ok=True)


def read_raw(path):
    if not path.exists() or path.stat().st_size == 0:
        return None, []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames, list(reader)


merged = {}
for name in COMMON + [scope_csv, "skipped_contexts.csv"]:
    header, rows = None, []
    for p in parts:
        h, r = read_raw(p / name)
        if h is None:
            continue
        if header is None:
            header = h
        assert h == header, (name, p, h, header)
        rows.extend(r)
    merged[name] = rows
    if name == scope_csv:
        rows.sort(key=lambda row: (row[scope_key], level_sort_key(row["level"])))
    write_csv(target / name, rows)
    print(f"[merge {FAMILY}] {name}: {len(rows)} rows")

# Trends from the merged summary (same row order as a monolithic run).
summary = merged["posterior_strategy_summary.csv"]
trends = strategy_budget_trends(summary, scope_key="context") if FAMILY != "lcbench" else strategy_budget_trends(summary)
write_csv(target / trend_csv, trends)
print(f"[merge {FAMILY}] {trend_csv}: {len(trends)} rows")


def typed(name):
    path = target / name
    return pd.read_csv(path).to_dict("records") if path.stat().st_size else []


scope_rows, hyp_rows, trend_rows = typed(scope_csv), typed("posterior_hypothesis_tests.csv"), typed(trend_csv)
if FAMILY == "energy":
    write_family_report(
        target / report, title="FSE 2026 posterior-risk revisit on the ENERGY (Twins) family",
        scope_noun="scenario", scope_rows=scope_rows, trend_rows=trend_rows, hypothesis_rows=hyp_rows,
        scope_key="scenario", srs_enabled=True, srs_seeds=100, include_oracles=False,
        intro_lines=[
            "This applies the FSE posterior-risk/posterior-confidence framework to the",
            "TwinsOrFalseFriends energy corpus. Each scenario is one (system, cost property,",
            "target property) combination; acquisition cost is the measured cost property",
            "(energy or runtime), so the same sampling question is asked under a different",
            "notion of cost. Posterior risk is relative to the measured configuration table.",
            "",
            "Source archive: Zenodo 7647208 (`TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip`).",
            f"Systems analyzed: `{', '.join(ALL_SYSTEMS)}`.",
            "Cost properties: `energy, performance`; target properties: `energy, performance`.",
            "Generated in independent per-scenario parts, merged by",
            "`merge_parts.py` in the original loop order.",
        ])
elif FAMILY == "workload":
    write_family_report(
        target / report, title="FSE 2026 posterior-risk revisit on the WORKLOAD family",
        scope_noun="context", scope_rows=scope_rows, trend_rows=trend_rows, hypothesis_rows=hyp_rows,
        scope_key="context_pair", srs_enabled=True, srs_seeds=100, include_oracles=False,
        intro_lines=[
            "This applies the FSE posterior-risk/posterior-confidence framework to the",
            "ICSE 2023 workload-impact corpus. Each context is one (system, workload)",
            "pair; the measured wall time (throughput for h2) is both the bound target",
            "and the empirical acquisition cost, so the analysis asks how posterior",
            "guarantees per cost react to workload/input context. Posterior risk is",
            "relative to the measured configuration table of that context.",
            "",
            "Source archive: Zenodo 7504284 (`artifact_excluding_raw_coverage.zip`).",
            f"Systems analyzed: `{', '.join(ALL_SYSTEMS)}`.",
            "Generated in independent per-context parts, merged by",
            "`merge_parts.py` in the original loop order.",
        ])
else:
    write_batch_report(
        target / report, workload_rows=scope_rows, trend_rows=trend_rows, hypothesis_rows=hyp_rows,
        workloads=[order(p) for p in parts], target_column="final_val_accuracy", cost_column="time_total",
        source_json="figshare file 21188598 (data_2k_lw.json)", srs_enabled=True, srs_seeds=30,
        include_oracles=False)
print(f"[merge {FAMILY}] wrote {target}")
