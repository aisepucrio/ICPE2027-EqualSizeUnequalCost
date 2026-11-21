# Traceability: paper → results → scripts

Every table, figure and number of the paper is derived from the per-corpus results under
`artifacts/`. This document lists, for each element, the file it comes from and the script
that produces it. Paths are relative to `artifacts/` unless stated otherwise.

## Result directories

| Directory | Content | Produced by |
|---|---|---|
| `fse_posterior_fse_artifact_final_t2/` | Kaltenecker corpus, original samples of Weis et al. at t2 | `scripts/run_fse_posterior_batch.py` |
| `fse_posterior_fse_artifact_final_t2_priorN/` | same with the prior-confidence exponent N instead of N+1 | `scripts/run_fse_posterior_batch.py --prior-offset 0` |
| `fse_posterior_x264_icpe_final/` | x264 corpus, t1–t3 | `scripts/run_fse_posterior_x264_batch.py` |
| `fse_posterior_energy_final/` | Energy corpus | `scripts/run_fse_posterior_twins_batch.py` |
| `fse_posterior_workload_final/` | Workload corpus | `scripts/run_fse_posterior_workload_batch.py` |
| `fse_posterior_lcbench_no_oracles_final/` | LCBench corpus | `scripts/run_fse_posterior_lcbench_batch.py` |
| `fse_posterior_linux_all_full/` | Linux corpus, full protocol | `scripts/run_linux_full_parts.sh` + `scripts/merge_linux_full_parts.py` |
| `fse_posterior_energy_equal_spend/` | equal-expenditure protocol, Energy | `scripts/run_energy_equal_spend.py` |
| `fse_posterior_lcbench_equal_spend/` | equal-expenditure protocol, LCBench | `scripts/run_lcbench_equal_spend.py` |
| `fse_posterior_synthesis/` | cross-corpus synthesis; Benjamini–Hochberg sensitivity | `scripts/build_fse_posterior_synthesis.py`, `scripts/mcc_sensitivity.py` |
| `paper_tables/` | Tables 3–7 and the numbers quoted in the text | `scripts/make_paper_tables.py` |
| `calibration/` | cost-to-size ratio per strategy and corpus | `scripts/make_calibration_table.py` |
| `paper_figures/` | Figures 1–8 | `scripts/make_paper_figures.py` |
| `srs_audit_note.md` | audit of the SRS implementation | `scripts/audit_srs_vs_artifact.py` |

Each corpus directory contains the same files: `posterior_strategy_summary.csv` (one row per
context, strategy and budget level: size and cost shares, cost-to-size ratio, posterior-risk
quantiles, integrated posterior confidence, and ω against the size-based and the cost-based
baselines), `posterior_hypothesis_tests.csv` (one row per scope and hypothesis: statistic,
p-value, effect size, verdict), a scope-level summary, `posterior_pareto.csv` and a report.
The hypothesis identifiers in these files map to the paper as follows: FSE1 = H1 (risk
differs), FSE5 = H2 (SRS < random), FSE6 = H3 (cost of SRS and random differs).

## Tables

| Paper | Content | Source | Script |
|---|---|---|---|
| Table 1 | characteristics of the six corpora | corpus descriptions (`data/README.md`); configuration counts in the scope summaries (`n_configurations`) | — |
| Table 2 | strategies, budgets, repetitions, scopes | protocol (README, *Protocol settings*); scope counts in Table 5 | — |
| Table 3 | ω/ω_max at N_2-wise, Kaltenecker | `fse_posterior_fse_artifact_final_t2/posterior_strategy_summary.csv` (`omega_size_over_max`) | `make_paper_tables.py` |
| Table 4 | RQ1 outcomes per corpus | `posterior_hypothesis_tests.csv` (FSE1, FSE5) and `posterior_strategy_summary.csv` of each corpus | `make_paper_tables.py` |
| Table 5 | decisions at equal size and at equal cost | same files; frontiers recomputed without diagnostic oracles | `make_paper_tables.py` |
| Table 6 | characteristics and outcomes per corpus | same files | `make_paper_tables.py` |
| Table 7 | H4 by tercile of r_max/r_min | `posterior_strategy_summary.csv` of each corpus | `make_paper_tables.py` |
| Section 4.2, footnote 1 | complete table of cost-to-size ratios | `posterior_strategy_summary.csv` (`median_calibration_ratio`) | `make_calibration_table.py` |

## Figures

| Paper | Content | Source | Script |
|---|---|---|---|
| Figure 1 | posterior risk against cost share of every BerkeleyDB sample at N = 97 | `fse_posterior_fse_artifact_final_t2/posterior_records.csv` (context `BerkeleyDBC`; `pct_cost`, `posterior_risk`, `strategy`) | `make_paper_figures.py` |
| Figure 2 | prior and posterior confidence per strategy, 7z, N = 600 | per-sample posterior risks in `fse_posterior_fse_artifact_final_t2/posterior_records.csv`, with `cost_sampling.posterior` (identical to the `posterior_confidence_curves.csv` written by the Kaltenecker run) | `make_paper_figures.py` |
| Figures 3, 4 | confidence discrepancy η per system and strategy | same | `make_paper_figures.py` |
| Figure 5 | ω/ω_max against N for SRS, uniform random and diversity-oriented sampling | `posterior_strategy_summary.csv` of each corpus (`omega_size_over_max`, `n`) | `make_paper_figures.py` |
| Figure 6 | size-based and cost-based frontier for BerkeleyDB and nginx | `fse_posterior_fse_artifact_final_t2/` and `fse_posterior_energy_final/posterior_strategy_summary.csv` | `make_paper_figures.py` |
| Figure 7 | pilotCost against uniform random at equal expenditure | `fse_posterior_{energy,lcbench}_equal_spend/equal_spend_scope_summary.csv` | `make_paper_figures.py` |
| Figure 8 | standing of SRS against N (H2, H5, equal expenditure) | hypothesis tests and strategy summaries of each corpus; equal-spend scope summaries | `make_paper_figures.py` |

## Numbers quoted in the text

| Paper | Number | Source |
|---|---|---|
| Abstract, §1, §4.1 | H1 in 713 of 851 scopes (83.8%) | `paper_tables/paper_tables.md` (Table 4, numbers quoted in the text) |
| §4.1 | BH correction: Workload 324 of 359, LCBench 101 of 210 | `fse_posterior_synthesis/multiple_comparison_sensitivity.md` |
| §4.1 | H2 restricted to N ≥ 32 (Energy 52 of 108, Workload 84 of 173) | `posterior_hypothesis_tests.csv` (FSE5, levels n32 and n64) |
| §4.1 | monotonicity, ω/ω_max of SRS and pilotCost per budget | `posterior_strategy_summary.csv` (`median_posterior_risk`, `omega_size_over_max`) |
| Abstract, §1, §4.2 | SRS more expensive in 285 of 313 scopes | `paper_tables/paper_tables.md` |
| §4.2 | cost-to-size ratios (pilotCost 0.71 / 0.83 / 0.65, etc.) | `calibration/calibration_ratio_table.md` |
| Abstract, §1, §4.2 | top recommendation changes in 24%, frontier in 97.3% | `paper_tables/paper_tables.md` (Table 5) |
| §4.2 | equal expenditure: pilotCost volume and risk ratios, wins against random, cap hits, winners | `fse_posterior_{energy,lcbench}_equal_spend/equal_spend_report.md` and `equal_spend_scope_summary.csv` |
| §4.3 | Spearman's ρ = 0.32; 5% vs 32% below and above r_max/r_min = 1.41; median spreads | `paper_tables/paper_tables.md` |
| §4.3 | SRS ahead of random at equal expenditure (Energy 75% at N = 32, 77% at N = 64) | `fse_posterior_energy_equal_spend/equal_spend_scope_summary.csv` (`srs_beats_random` per `ref_level`) |
| §3.2.2 | SRS implementation audited against the original notebook | `srs_audit_note.md` |
| §5 | prior exponent N vs N+1: identical decisions | `fse_posterior_fse_artifact_final_t2_priorN/` |
