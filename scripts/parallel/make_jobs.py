#!/usr/bin/env python3
"""Split the Energy, Workload and LCBench runs (fixed size and equal expenditure) into
independent jobs, one per scenario, context or dataset.

Writes <work-dir>/jobs.txt with one `name|command` line per job (233 jobs). Each job runs the
same script with the same protocol parameters as the single-process commands in the README,
restricted to one system, context or dataset; `merge_parts.py` then concatenates the fixed-size
parts in the single-process loop order. LCBench min-max-scales its features over all datasets,
so the full LCBench table is parsed once and cached (`lcbench_cached.py`), and each part
restricts the rows only after encoding.

Usage:
  python scripts/parallel/make_jobs.py --work-dir WORK [--data-dir data/raw] [--python python3]
Then:
  tr '\\n' '\\0' < WORK/jobs.txt | WORK=WORK xargs -0 -P 8 -n 1 scripts/parallel/run_job.sh
"""
from __future__ import annotations

import argparse
import pickle
import re
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "scripts")]
import cost_sampling.generated_sampling as G  # noqa: E402
from run_fse_posterior_twins_batch import ALL_SYSTEMS as ENERGY_SYSTEMS  # noqa: E402
from run_fse_posterior_workload_batch import ALL_SYSTEMS as WORKLOAD_SYSTEMS  # noqa: E402

ENERGY_ZIP = "TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip"
WORKLOAD_ZIP = "artifact_excluding_raw_coverage.zip"
LCBENCH_JSON = "data_2k_lw.json"
# Largest pools first, so that the tail of a parallel run is short.
ENERGY_ORDER = ["7z", "LLVM", "VP8", "exastencils", "Apache", "x264", "PostgreSQL", "MongoDB",
                "jump3r", "nginx", "kanzi", "lrzip", "brotli", "HSQLDB"]


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_") or "value"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=REPO / "data" / "raw")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    assert sorted(ENERGY_ORDER) == sorted(ENERGY_SYSTEMS)

    data, work = args.data_dir.resolve(), args.work_dir.resolve()
    energy_zip, workload_zip, lcbench_json = data / ENERGY_ZIP, data / WORKLOAD_ZIP, data / LCBENCH_JSON
    for path in (energy_zip, workload_zip, lcbench_json):
        if not path.exists():
            raise SystemExit(f"missing input {path}; see data/README.md")
    parts = work / "parts"
    cache = work / "lcbench_table.pkl"
    work.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        print(f"parsing {lcbench_json} once (a few minutes)")
        table = G.load_lcbench_table(str(lcbench_json), runtime_mode="last")
        with open(cache, "wb") as fh:
            pickle.dump(table, fh, protocol=pickle.HIGHEST_PROTOCOL)
    with open(cache, "rb") as fh:
        datasets = sorted({row["workload"] for row in pickle.load(fh).rows})

    py = f"{shlex.quote(args.python)} -I"
    cached = f"{py} scripts/parallel/lcbench_cached.py {shlex.quote(str(REPO))} {shlex.quote(str(cache))}"
    common = "--extreme max --prior-offset 1 --no-figures"
    q = lambda p: shlex.quote(str(p))  # noqa: E731
    jobs = []
    for s in ENERGY_ORDER:
        for cost in ("energy", "performance"):
            for target in ("energy", "performance"):
                jobs.append((f"en_{s}_{cost}_{target}",
                             f"{py} scripts/run_fse_posterior_twins_batch.py --zip {q(energy_zip)} --systems {s} "
                             f"--target-props {target} --cost-props {cost} --levels n8,n16,n32,n64 --seeds 100 "
                             f"--srs-seeds 100 --no-oracles {common} --output-dir {q(parts / 'energy' / f'{s}__{cost}__{target}')}"))
    for s in WORKLOAD_SYSTEMS:
        table = G.load_workload_table(str(workload_zip), s, where={})
        for w in sorted({row["workload"] for row in table.rows}):
            assert "," not in w
            jobs.append((f"wl_{s}_{slug(w)}",
                         f"{py} scripts/run_fse_posterior_workload_batch.py --zip {q(workload_zip)} --systems {s} "
                         f"--workloads {shlex.quote(w)} --levels n8,n16,n32,n64 --seeds 100 --srs-seeds 100 "
                         f"--no-oracles {common} --output-dir {q(parts / 'workload' / f'{s}__{slug(w)}')}"))
    for d in datasets:
        jobs.append((f"lc_{slug(d)}",
                     f"{cached} scripts/run_fse_posterior_lcbench_batch.py --json {q(lcbench_json)} "
                     f"--datasets {shlex.quote(d)} --target-column final_val_accuracy --cost-column time_total "
                     f"--runtime-mode last --max-budget 64 --seeds 30 --srs-seeds 30 --no-oracles {common} "
                     f"--output-dir {q(parts / 'lcbench' / slug(d))}"))
    for s in ENERGY_ORDER:
        jobs.append((f"eqen_{s}", f"{py} scripts/run_energy_equal_spend.py --zip {q(energy_zip)} --systems {s} "
                                  f"--output-dir {q(work / 'equal_spend_energy')}"))
    for d in datasets:
        jobs.append((f"eqlc_{slug(d)}", f"{cached} scripts/run_lcbench_equal_spend.py --json {q(lcbench_json)} "
                                        f"--datasets {shlex.quote(d)} --output-dir {q(work / 'equal_spend_lcbench')}"))
    (work / "jobs.txt").write_text("".join(f"{name}|{cmd}\n" for name, cmd in jobs))
    counts = {k: sum(n.startswith(k + "_") for n, _ in jobs) for k in ("en", "wl", "lc", "eqen", "eqlc")}
    print(f"wrote {len(jobs)} jobs to {work / 'jobs.txt'}: {counts}")


if __name__ == "__main__":
    main()
