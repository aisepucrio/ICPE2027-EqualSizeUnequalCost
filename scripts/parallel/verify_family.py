#!/usr/bin/env python3
"""Compare a regenerated result directory with the committed one.

Prints, per strategy, the largest absolute difference over the key summary columns, and the
number of scopes that support each hypothesis in both directories.

Usage: python scripts/parallel/verify_family.py <committed_dir> <regenerated_dir>
"""
import sys

import numpy as np
import pandas as pd

committed, regenerated = sys.argv[1], sys.argv[2]
KEY = ["context", "strategy", "level"]
COLS = ["median_calibration_ratio", "median_posterior_risk", "omega_size_baseline", "omega_cost_baseline",
        "median_pct_cost", "posterior_confidence_area"]
com = pd.read_csv(f"{committed}/posterior_strategy_summary.csv")
new = pd.read_csv(f"{regenerated}/posterior_strategy_summary.csv")
same = set(map(tuple, com[KEY].values)) == set(map(tuple, new[KEY].values))
print(f"rows committed {len(com)} regenerated {len(new)}; same keys: {same}")
merged = com.merge(new, on=KEY, suffixes=("_c", "_n"))
for strategy, g in merged.groupby("strategy"):
    diff = max(float(np.nanmax(np.abs(g[c + "_c"] - g[c + "_n"]))) for c in COLS)
    print(f"  {strategy:12s} rows {len(g):4d}  max |diff| over key columns: {diff:.2e}")
ht_c = pd.read_csv(f"{committed}/posterior_hypothesis_tests.csv")
ht_n = pd.read_csv(f"{regenerated}/posterior_hypothesis_tests.csv")
for h in sorted(ht_c.hypothesis.unique()):
    a = int((ht_c[ht_c.hypothesis == h].verdict == "supports").sum())
    b = int((ht_n[ht_n.hypothesis == h].verdict == "supports").sum())
    print(f"  {h}: supports committed {a} -> regenerated {b}")
