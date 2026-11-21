#!/usr/bin/env python3
"""Download the TuxKConfig kernel-size pools from OpenML and store one parquet per release.

`cost_sampling/linux_data.py` reads data/raw/linux/tuxkconfig_<release>.parquet: one row per
configuration, one uint8 column per Kconfig option, and the columns in NON_OPTION_COLUMNS
(the vmlinux size, its compressed-image variants, active_options, cid). The OpenML column names
are used unchanged; only the option columns are cast to uint8.

OpenML returns float64 columns, so the largest release (4.13, 92,562 x 9,488) needs about 7 GB
of memory before the cast. Convert one release per invocation on smaller machines.

Requires: pip install openml pyarrow

Usage:
  python scripts/convert_tuxkconfig_openml.py --releases 413 415 420 500 504 507 508
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from cost_sampling.linux_data import NON_OPTION_COLUMNS  # noqa: E402

OPENML_IDS = {"413": 46759, "415": 46739, "420": 46740, "500": 46741,
              "504": 46742, "507": 46743, "508": 46744}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--releases", nargs="+", default=list(OPENML_IDS), choices=list(OPENML_IDS))
    parser.add_argument("--out-dir", type=Path, default=REPO / "data" / "raw" / "linux")
    args = parser.parse_args()
    import openml  # imported here so that the rest of the repository does not depend on it

    args.out_dir.mkdir(parents=True, exist_ok=True)
    non_options = set(NON_OPTION_COLUMNS)
    for release in args.releases:
        out = args.out_dir / f"tuxkconfig_{release}.parquet"
        if out.exists():
            print(f"{out} exists, skipping")
            continue
        df, *_ = openml.datasets.get_dataset(OPENML_IDS[release], download_data=True).get_data()
        options = [c for c in df.columns if c not in non_options]
        df[options] = df[options].astype("uint8")
        df.to_parquet(out, index=False)
        print(f"release {release}: {df.shape[0]} configurations, {len(options)} options -> {out}")


if __name__ == "__main__":
    main()
