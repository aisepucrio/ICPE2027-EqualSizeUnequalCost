"""Run an LCBench script with load_lcbench_table served from a pickled full table.

The pickle holds the table of ALL datasets, encoded as in a monolithic run (min-max over all rows).
If the caller passes `datasets`, rows are restricted AFTER encoding, so X is identical to the
monolithic run's rows. Usage:
  python lcbench_cached.py <repo_root> <table.pkl> <script.py> <script args...>
  python lcbench_cached.py <repo_root> <table.pkl> --build <data_2k_lw.json>
"""
import pickle
import runpy
import sys
from pathlib import Path

import numpy as np

REPO, PKL = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO)
sys.path.insert(0, str(Path(REPO) / "scripts"))
import cost_sampling.generated_sampling as G  # noqa: E402

if sys.argv[3] == "--build":
    table = G.load_lcbench_table(sys.argv[4], runtime_mode="last")
    with open(PKL, "wb") as fh:
        pickle.dump(table, fh, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"cached {len(table.rows)} rows, X {table.X.shape}")
    sys.exit(0)

with open(PKL, "rb") as fh:
    FULL = pickle.load(fh)


def cached_load_lcbench_table(json_path, *, datasets=None, where=None, max_rows=None, row_seed=0,
                              runtime_tag="time", runtime_mode="last"):
    assert runtime_mode == "last" and runtime_tag == "time" and not where and max_rows is None
    if not datasets:
        return FULL
    keep = set(datasets)
    idx = np.asarray([i for i, r in enumerate(FULL.rows) if r["workload"] in keep], dtype=int)
    missing = keep - {FULL.rows[i]["workload"] for i in idx}
    if missing:
        raise ValueError(f"datasets not found: {sorted(missing)}")
    return G.subset_measured_table(FULL, idx)


G.load_lcbench_table = cached_load_lcbench_table
script = sys.argv[3]
sys.argv = [script] + sys.argv[4:]
runpy.run_path(script, run_name="__main__")
