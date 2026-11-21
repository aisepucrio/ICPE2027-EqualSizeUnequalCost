# Equal Size, Unequal Cost: A Cost-Aware Replication of Posterior Guarantees for Configuration Sampling Strategies

Replication package of the paper of the same title, submitted to the ACM/SPEC International
Conference on Performance Engineering (ICPE 2027). The paper is under double-blind review;
the authors' names are withheld.

The package contains the analysis code, the committed results from which every number of
the paper is derived, scripts that regenerate all tables and figures of the paper from these
results, and a protocol to retrieve the six public corpora and rerun the complete study.

## About the study

Configuration sampling strategies are commonly compared by the performance bounds they yield
at a fixed sample size, which implicitly treats the number of sampled configurations as a
proxy for measurement effort. In practice, measurement cost varies by up to two orders of
magnitude within a single system, and strategies differ in the regions of the configuration
space they favor.

The study replicates the probabilistic framework of Weis et al. (FSE 2026), which evaluates
sampling strategies by the posterior risk and confidence of their worst-case bounds, and
extends it to measured acquisition cost. It reproduces the original analyses on the original
data, tests the generality of their four central claims on five further corpora spanning
configurable software and hyperparameter optimization, and compares strategies at equal
measured cost instead of equal sample size through a cost-based confidence discrepancy, a
Pareto analysis of guarantee versus expenditure, and an equal-expenditure protocol.

### Research questions

- **RQ1.** To what extent do the findings of Weis et al. on posterior risk and confidence
  replicate on their corpora and generalize to further corpora at a fixed sample size?
- **RQ2.** To what extent do the recommendations derived from posterior guarantees change
  when strategies are compared at equal cost instead of equal size?
- **RQ3.** What explains when comparing strategies at equal cost instead of equal size
  changes the recommendations derived from posterior guarantees?

### Main results

| Result | Value | Source in this package |
|---|---|---|
| Decision scopes, over six corpora | 851 | `artifacts/paper_tables/paper_tables.md` (Table 5) |
| Posterior risk discriminates between strategies (H1) | 713 of 851 scopes (83.8%) | Table 4 |
| SRS is the more expensive strategy where its cost differs from uniform random | 285 of 313 scopes | `artifacts/paper_tables/paper_tables.md` (numbers quoted in the text) |
| Comparing at equal cost changes the top recommendation (H4) | 200 of 851 scopes (24%) | Table 5 |
| Comparing at equal cost changes the Pareto frontier (H6) | 828 of 851 scopes (97.3%) | Table 5 |
| Top recommendation changes when strategies spend similarly (r_max/r_min ≤ 1.41) | 5%, against 32% otherwise | Table 7 |
| pilotCost at equal expenditure, Energy (target = cost) | 1.66× the configurations, 1.5× the posterior risk of uniform random | `artifacts/fse_posterior_energy_equal_spend/` |

### Corpora

| Corpus | Subjects | Configurations | Target / cost | Role in the study |
|---|---|---|---|---|
| Kaltenecker | 7 systems | 1,024–193,536 | performance / same | Close replication of Weis et al. |
| x264 | 1 system, 17 inputs | 1,152 | time or size / time | Replication; identical and asymmetric settings |
| Energy | 14 systems | 180–86,058 | energy or runtime / energy or runtime | Alternative notion of cost |
| Workload | 9 systems, 93 contexts | 191–6,764 | execution time / same | Dependence on the workload |
| LCBench | 35 datasets | 2,000 | accuracy / training time | Outside configurable software; weak coupling |
| Linux | 7 releases | 19,952–92,562 | image size / same | Large-scale stress test on measured pools |

Sources, DOIs and download commands for every corpus are in [`data/README.md`](data/README.md).

## Repository layout

```
cost_sampling/          core package: loaders, samplers (incl. SRS), posterior risk and
                        confidence, Pareto analysis, hypothesis tests
scripts/
  run_fse_posterior_batch.py           Kaltenecker corpus (data of Weis et al.)
  run_fse_posterior_x264_batch.py      x264 corpus
  run_fse_posterior_twins_batch.py     Energy corpus
  run_fse_posterior_workload_batch.py  Workload corpus
  run_fse_posterior_lcbench_batch.py   LCBench corpus
  run_fse_posterior_linux_batch.py     Linux corpus (+ run_linux_full_parts.sh, merge_linux_full_parts.py)
  run_energy_equal_spend.py            equal-expenditure protocol, Energy
  run_lcbench_equal_spend.py           equal-expenditure protocol, LCBench
  build_fse_posterior_synthesis.py     cross-corpus synthesis
  mcc_sensitivity.py                   Benjamini–Hochberg sensitivity of the hypothesis tests
  audit_srs_vs_artifact.py             audit of our SRS implementation against the original one
  make_paper_tables.py                 Tables 3–7 of the paper
  make_calibration_table.py            cost-to-size ratio per strategy and corpus (Section 4.2)
  make_paper_figures.py                Figures 1–8 of the paper
  build_x264_allruns_zip.py            data preparation, x264 corpus
  convert_tuxkconfig_openml.py         data preparation, Linux corpus
  parallel/                            optional: split the long runs into independent jobs
artifacts/              committed results (one directory per corpus and protocol)
data/README.md          data retrieval protocol; raw data goes to data/raw/ (git-ignored)
docs/TRACEABILITY.md    every table, figure and quoted number -> result file -> script
tests/                  unit test of the cost-aware sampler
```

## Setup

The code requires Python 3.13 or later.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the versions used to produce the committed results. The Linux corpus
additionally requires `pyarrow` and `scikit-learn` (included), and its data preparation the
`openml` package (`pip install openml`).

## Quick start: check the paper against the committed results

These commands need no download. They read the committed results under `artifacts/` and run
in seconds.

```bash
python scripts/make_paper_tables.py         # Tables 3-7       -> artifacts/paper_tables/
python scripts/make_calibration_table.py    # ratio r per strategy and corpus -> artifacts/calibration/
python scripts/make_paper_figures.py        # Figures 1-8      -> artifacts/paper_figures/
python scripts/mcc_sensitivity.py           # BH sensitivity   -> artifacts/fse_posterior_synthesis/
python scripts/build_fse_posterior_synthesis.py   # cross-corpus synthesis
python tests/test_pilot_cost_sample.py      # unit test
```

Each script prints what it writes. `git status` should show no change afterwards: the
committed outputs are exactly what these scripts produce.

## Full reproduction from the raw data

### 1. Retrieve the data

Follow [`data/README.md`](data/README.md). It places the six corpora under `data/raw/`.

### 2. Run the corpora

The commands below write into `artifacts/_repro/` (git-ignored), using the directory names
of the committed results, so that each regenerated directory can be compared with its
committed counterpart (step 5). They reproduce the protocol of the paper exactly; omit
`--no-figures` to also obtain per-context diagnostic figures.

```bash
REPRO=artifacts/_repro

# Kaltenecker: the original samples of Weis et al. at t2, including their SRS runs
python scripts/run_fse_posterior_batch.py --fse-root data/raw/fse_artifact/data \
  --contexts ALL --strategies random,solverBased,divDistBased,twise,SRSSampling \
  --levels t2 --max-runs 100 --extreme max --prior-offset 1 \
  --output-dir $REPRO/fse_posterior_fse_artifact_final_t2
#   sensitivity to the prior-confidence exponent (N instead of N+1): same with
#   --prior-offset 0 --output-dir $REPRO/fse_posterior_fse_artifact_final_t2_priorN

# x264: original samples at t1-t3, SRS generated with 100 seeds; encoding time is the cost
python scripts/run_fse_posterior_x264_batch.py --runs-zip data/raw/AllRuns.zip \
  --contexts 0-16 --target-props time,size --cost-prop time \
  --strategies random,solverBased,divDistBased,twise,distBased,henard \
  --levels t1,t2,t3 --fixed-level t2 --max-runs 100 --srs-seeds 100 \
  --extreme max --prior-offset 1 --output-dir $REPRO/fse_posterior_x264_icpe_final

# Energy: 14 systems x {energy, runtime} as target x {energy, runtime} as cost
python scripts/run_fse_posterior_twins_batch.py \
  --zip data/raw/TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip \
  --systems ALL --target-props energy,performance --cost-props energy,performance \
  --levels n8,n16,n32,n64 --seeds 100 --srs-seeds 100 --no-oracles \
  --extreme max --prior-offset 1 --no-figures --output-dir $REPRO/fse_posterior_energy_final

# Workload: 9 systems, 93 system-workload contexts
python scripts/run_fse_posterior_workload_batch.py \
  --zip data/raw/artifact_excluding_raw_coverage.zip \
  --systems ALL --workloads ALL --levels n8,n16,n32,n64 --seeds 100 --srs-seeds 100 \
  --no-oracles --extreme max --prior-offset 1 --no-figures \
  --output-dir $REPRO/fse_posterior_workload_final

# LCBench: 35 datasets; final validation accuracy as target, training time as cost
python scripts/run_fse_posterior_lcbench_batch.py --json data/raw/data_2k_lw.json \
  --datasets ALL --target-column final_val_accuracy --cost-column time_total \
  --runtime-mode last --max-budget 64 --seeds 30 --srs-seeds 30 --no-oracles \
  --extreme max --prior-offset 1 --no-figures \
  --output-dir $REPRO/fse_posterior_lcbench_no_oracles_final
```

On a 10-core laptop, the Kaltenecker run takes about 10 seconds and the x264 run about
1.5 minutes. In a single process, the Energy and Workload runs take about one and one and
a half hours (roughly one minute per scenario or context) and LCBench about a quarter of an
hour; see *Optional: parallel execution* below.

**Linux.** The Linux corpus is the most demanding step. It is run one release at a time;
the script skips releases that are already complete, so it can simply be restarted after an
interruption. The parts are then merged:

```bash
sh scripts/run_linux_full_parts.sh          # writes artifacts/fse_posterior_linux_full_parts/r<release>/
python scripts/merge_linux_full_parts.py \
  --parts-dir artifacts/fse_posterior_linux_full_parts \
  --output-dir $REPRO/fse_posterior_linux_all_full
```

Each Linux release uses budgets of 1%, 2% and 5% of the pool, 100 runs of the stochastic
strategies, 20 runs of the diversity, uncertainty and coverage samplers, and 100 SRS seeds.
Set `PYTHON` to choose the interpreter used by the shell script.

### 3. Run the equal-expenditure protocol

Each strategy acquires as many configurations as a fixed measured budget permits
(B = n_ref × mean pool cost, n_ref ∈ {8, 16, 32, 64}; 30 seeds).

```bash
python scripts/run_energy_equal_spend.py \
  --zip data/raw/TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip --systems ALL \
  --output-dir $REPRO/fse_posterior_energy_equal_spend
python scripts/run_lcbench_equal_spend.py --json data/raw/data_2k_lw.json --datasets ALL \
  --output-dir $REPRO/fse_posterior_lcbench_equal_spend
```

Both scripts save one checkpoint per system or dataset (`parts/`) and resume from them. Each
Energy system takes about four minutes and each LCBench dataset about three.

### 4. Rebuild the synthesis, tables and figures

```bash
python scripts/build_fse_posterior_synthesis.py \
  --fse-dir $REPRO/fse_posterior_fse_artifact_final_t2 --x264-dir $REPRO/fse_posterior_x264_icpe_final \
  --energy-dir $REPRO/fse_posterior_energy_final --workload-dir $REPRO/fse_posterior_workload_final \
  --linux-dir $REPRO/fse_posterior_linux_all_full --lcbench-dir $REPRO/fse_posterior_lcbench_no_oracles_final \
  --output-dir $REPRO/fse_posterior_synthesis
python scripts/make_paper_tables.py      --artifacts $REPRO --out $REPRO/paper_tables
python scripts/make_calibration_table.py --artifacts $REPRO --out $REPRO/calibration
python scripts/make_paper_figures.py     --artifacts $REPRO --out $REPRO/paper_figures
```

`scripts/mcc_sensitivity.py` reads the committed directories; to apply it to a regeneration,
copy the regenerated directories over the committed ones (git shows any difference).

### 5. Compare a regeneration with the committed results

```bash
python scripts/parallel/verify_family.py artifacts/fse_posterior_energy_final \
  $REPRO/fse_posterior_energy_final
```

It reports, per strategy, the largest difference over the key summary columns, and the
number of scopes supporting each hypothesis in both directories.

### Optional: parallel execution

The Energy, Workload and LCBench runs (fixed size and equal expenditure) can take hours in a
single process. `scripts/parallel/` splits them into 233 independent jobs (one per scenario,
context or dataset) with the same protocol parameters, and merges the parts in the
single-process loop order:

```bash
WORK=artifacts/_repro/parallel
python scripts/parallel/make_jobs.py --work-dir $WORK          # writes $WORK/jobs.txt
tr '\n' '\0' < $WORK/jobs.txt | WORK=$WORK xargs -0 -P 8 -n 1 scripts/parallel/run_job.sh
for family in energy workload lcbench; do
  python scripts/parallel/merge_parts.py . $WORK/parts $WORK/merged $family
done
# aggregate the equal-expenditure checkpoints (all parts are done, so nothing is recomputed)
python scripts/run_energy_equal_spend.py --zip data/raw/TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip \
  --systems ALL --output-dir $WORK/equal_spend_energy
python scripts/parallel/lcbench_cached.py . $WORK/lcbench_table.pkl scripts/run_lcbench_equal_spend.py \
  --json data/raw/data_2k_lw.json --datasets ALL --output-dir $WORK/equal_spend_lcbench
```

`run_job.sh` logs each job to `$WORK/logs/` and skips completed jobs on a restart. LCBench
min-max-scales its features over all datasets, so the full table is parsed once and cached
(`lcbench_cached.py`); each LCBench job restricts the rows only after the encoding, which
keeps every part identical to the corresponding rows of a single-process run.

## Protocol settings

| Setting | Value |
|---|---|
| Bound | worst case (`--extreme max`) |
| Prior confidence | exponent N+1 of the original code (`--prior-offset 1`); N gives identical decisions (`*_priorN`) |
| Budgets | t2 (= N_2-wise) for Kaltenecker; t1–t3 for x264 (headline at t2); N ∈ {8, 16, 32, 64} for Energy and Workload; N ∈ {8, 16, 20, 32, 40, 64} for LCBench; 1%, 2%, 5% of the pool for Linux |
| Repetitions | 100 (LCBench and the equal-expenditure protocol: 30) |
| SRS | step 25, Welch's t-test (p < 0.05), random fill; the original SRS samples for Kaltenecker |
| De-duplication | all samples, including those of the original package, before size and cost are computed |
| Diagnostic oracles | excluded from all reported results (`--no-oracles`) |
| Pool-relative risk | Linux and LCBench: posterior risk relative to the measured pool |
| Multiple testing | Benjamini–Hochberg, FDR 0.05, within each (corpus, hypothesis) family |

## Mapping between the paper and this package

[`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) lists, for every table, figure and number
quoted in the paper, the result file it comes from and the script that produces it.

## Notes on reproducibility

- All sampling is seeded, and a regeneration with the pinned environment reproduces the
  committed results. The data protocol has been executed end to end from the original
  archives: the published checksums match, and the Kaltenecker and x264 runs as well as
  sample jobs of every other family (Energy, Workload, LCBench, equal expenditure) reproduce
  the committed results exactly.
- At small budgets (N ≤ 32), SRS performs at most one recursion step, and SRS and uniform
  random sampling can reach exactly the same median posterior risk. Whether `<` holds for
  such a tie can depend on floating-point rounding, which differs across machines. Two counts
  of the paper are affected by such ties: SRS on the cost-based frontier (288 of 851 scopes;
  286 if the two tied Energy scopes resolve the other way) and SRS ahead of uniform random at
  equal expenditure on Energy at N = 32 (75%; 71% otherwise).
- On Linux and LCBench, posterior risk refers to the measured pool rather than to the complete
  configuration space.

## License

The code (`cost_sampling/`, `scripts/`, `tests/`) is released under the MIT License (see
`LICENSE`). The datasets are not redistributed; they remain under the terms of their original
publications (see `data/README.md`).
