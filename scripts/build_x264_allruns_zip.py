#!/usr/bin/env python3
"""Build data/raw/AllRuns.zip (x264 sample sets) from a clone of the ICPE'20 package.

The upstream package (https://github.com/jualvespereira/ICPE2020) stores the sampled training
sets of the x264 study under

  Distance-Based_Data_{Size,Time}/SupplementaryWebsite/PerformancePredictions/AllExperiments/
      x264_<i>/x264_<i>_<run>/sampledConfigurations_<strategy>_t<level>.csv

The loader (`cost_sampling/archive_runs.py`) expects one context per (input, property):

  AllRuns/x264_{size,time}_<i>/x264_<i>_<run>/sampledConfigurations_<strategy>_t<level>.csv

This script only re-roots the files; their content is unchanged. Entries are written in sorted
order with a fixed timestamp, so the archive is identical across runs.

Usage:
  git clone --depth 1 https://github.com/jualvespereira/ICPE2020.git /tmp/ICPE2020
  python scripts/build_x264_allruns_zip.py /tmp/ICPE2020 data/raw/AllRuns.zip
"""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

PATTERN = re.compile(
    r"Distance-Based_Data_(?P<prop>Size|Time)/SupplementaryWebsite/PerformancePredictions/AllExperiments/"
    r"x264_(?P<input>\d+)/(?P<run>x264_\d+_\d+)/(?P<file>sampledConfigurations_[^/]+\.csv)$"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("upstream", type=Path, help="root of the ICPE2020 clone")
    parser.add_argument("output", type=Path, help="zip to write, e.g. data/raw/AllRuns.zip")
    args = parser.parse_args()

    members = []
    for path in args.upstream.rglob("sampledConfigurations_*.csv"):
        rel = path.relative_to(args.upstream).as_posix()
        match = PATTERN.search(rel)
        if match:
            arcname = (f"AllRuns/x264_{match['prop'].lower()}_{match['input']}/"
                       f"{match['run']}/{match['file']}")
            members.append((arcname, path))
    if not members:
        raise SystemExit(f"no x264 sample sets found under {args.upstream}")
    members.sort()
    contexts = sorted({m[0].split("/")[1] for m in members})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for arcname, path in members:
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(f"wrote {len(members)} sample files for {len(contexts)} contexts to {args.output}")


if __name__ == "__main__":
    main()
