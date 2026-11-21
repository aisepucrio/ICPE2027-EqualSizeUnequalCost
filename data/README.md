# Data: sources, retrieval, and expected layout

This study analyses six public corpora. **No measurement data is redistributed in this
repository**: every input is retrieved from its original archive with the commands below.
Only the results derived from the data are committed (under `artifacts/`), so the paper's
tables and figures can be checked without any download (see the top-level README,
*Quick start*).

All commands are run from the repository root and place the inputs under `data/raw/`
(ignored by git). The analysis scripts default to these locations; every path can also be
passed explicitly (`--fse-root`, `--runs-zip`, `--zip`, `--json`).

## Overview

| # | Corpus | Original study | Archive | Download | Expected location |
|---|---|---|---|---|---|
| 1 | Kaltenecker | Weis et al., FSE 2026 (data of Kaltenecker et al., ICSE 2019) | Zenodo [10.5281/zenodo.19682296](https://doi.org/10.5281/zenodo.19682296) | 162 MB | `data/raw/fse_artifact/data/sampling/` |
| 2 | x264 | Pereira et al., ICPE 2020 | GitHub [jualvespereira/ICPE2020](https://github.com/jualvespereira/ICPE2020) | ~1.7 GB clone | `data/raw/AllRuns.zip` (built) |
| 3 | Energy | Weber et al., ICSE 2023 | Zenodo [10.5281/zenodo.7647208](https://doi.org/10.5281/zenodo.7647208) | 104 MB | `data/raw/TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip` |
| 4 | Workload | Mühlbauer et al., ICSE 2023 | Zenodo [10.5281/zenodo.7504284](https://doi.org/10.5281/zenodo.7504284) | 390 MB | `data/raw/artifact_excluding_raw_coverage.zip` |
| 5 | LCBench | Zimmer et al., TPAMI 2021 | figshare file [21188598](https://ndownloader.figshare.com/files/21188598) | 339 MB (975 MB unzipped) | `data/raw/data_2k_lw.json` |
| 6 | Linux | Borges et al., EASE 2025 (TuxKConfig) | OpenML datasets 46739–46744, 46759 | several GB | `data/raw/linux/tuxkconfig_<release>.parquet` |

Corpora 1, 3, 4 and 5 are single downloads. Corpus 2 requires a re-rooting step and
corpus 6 a format conversion; both are scripted below.

```bash
mkdir -p data/raw
```

The MD5 checksums below are the ones published by Zenodo. Verify with `md5sum <file>`
(Linux) or `md5 -q <file>` (macOS).

## 1. Kaltenecker: replication package of Weis et al.

Seven exhaustively measured configurable systems (7z, BerkeleyDB, Dune, HIPAcc, JavaGC, LLVM,
Polly) with the sample sets of all strategies evaluated by Weis et al., including their SRS
runs. We reuse the measurement tables and the sample sets unchanged.

- Weis, Maggio, Siegmund, Apel. *Evaluating Risk and Confidence in Performance Bounds of
  Configuration Sampling Strategies.* Proc. ACM Softw. Eng. 3, FSE (2026).
- Replication package: *Risk and Confidence in Performance Bounds of Configuration Sampling
  Strategies — Sources and Data.* doi:10.5281/zenodo.19682296 (CC BY 4.0).
- Original measurements: Kaltenecker et al., *Distance-Based Sampling of Software
  Configuration Spaces*, ICSE 2019, doi:10.1109/ICSE.2019.00112.

```bash
mkdir -p data/raw/fse_artifact
curl -fL -o data/raw/fse_artifact/data.zip \
  "https://zenodo.org/api/records/19682296/files/data.zip/content"
# MD5 33831a921413d96ac484b6ce13cd710d (161,755,775 bytes)
```

The archive contains `data/sampling/<system>/measurements.csv` and one directory per run with
`sampledConfigurations_<strategy>_<level>.csv`. Only the measurement tables and the `t2`
samples of the five strategies used in the paper are needed, so a selective extraction keeps
the disk footprint small:

```bash
cd data/raw/fse_artifact
unzip -q data.zip 'data/sampling/*/measurements.csv' \
  'data/sampling/*/*/sampledConfigurations_random_t2.csv' \
  'data/sampling/*/*/sampledConfigurations_solverBased_t2.csv' \
  'data/sampling/*/*/sampledConfigurations_divDistBased_t2.csv' \
  'data/sampling/*/*/sampledConfigurations_twise_t2.csv' \
  'data/sampling/*/*/sampledConfigurations_SRSSampling_t2.csv'
cd ../../..
```

(`unzip -q data.zip` extracts everything and works as well.) The runner is then pointed at
`--fse-root data/raw/fse_artifact/data`.

## 2. x264: sample sets of Pereira et al.

The x264 video encoder, 1,152 configurations measured on 17 input videos for encoding time
and output size, with the sample sets of six strategies at three t-wise budget levels
(100 runs each).

- Pereira, Acher, Martin, Jézéquel. *Sampling Effect on Performance Prediction of Configurable
  Systems: A Case Study.* ICPE 2020, doi:10.1145/3358960.3379137.

The upstream repository stores the sample sets per input under
`Distance-Based_Data_{Size,Time}/SupplementaryWebsite/PerformancePredictions/AllExperiments/`.
`scripts/build_x264_allruns_zip.py` copies them, unchanged, into the single archive layout the
loader reads (`AllRuns/x264_{time,size}_<input>/x264_<input>_<run>/...`). The clone expands
to about 1.7 GB because of its many small files; it can be deleted once the archive is built.

```bash
git clone --depth 1 https://github.com/jualvespereira/ICPE2020.git /tmp/ICPE2020
python scripts/build_x264_allruns_zip.py /tmp/ICPE2020 data/raw/AllRuns.zip
rm -rf /tmp/ICPE2020    # optional
```

The loader reconstructs the measured configuration table from the sample sets themselves, so
no further file is needed.

## 3. Energy: Twins or False Friends

Fourteen configurable systems with both energy and runtime measurements per configuration.

- Weber, Kaltenecker, Sattler, Apel, Siegmund. *Twins or False Friends? A Study on Energy
  Consumption and Performance of Configurable Software.* ICSE 2023,
  doi:10.1109/ICSE48619.2023.00177.

```bash
curl -fL -o data/raw/TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip \
  "https://zenodo.org/api/records/7647208/files/AI-4-SE/TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip/content"
# MD5 e5fe602249e5d981e5a3524f083d4b55 (104,064,529 bytes)
```

The runners read `data/<system>/measurements.csv` directly from the zip; no extraction is
needed.

## 4. Workload: impact of workloads on configurable systems

Nine configurable systems (batik, dconvert, h2, jump3r, kanzi, lrzip, x264, xz, z3) measured
under several workloads, 93 system–workload contexts in total.

- Mühlbauer, Sattler, Kaltenecker, Dorn, Apel, Siegmund. *Analysing the Impact of Workloads on
  Modeling the Performance of Configurable Software Systems.* ICSE 2023,
  doi:10.1109/ICSE48619.2023.00176.

```bash
curl -fL -o data/raw/artifact_excluding_raw_coverage.zip \
  "https://zenodo.org/api/records/7504284/files/artifact_excluding_raw_coverage.zip/content"
# MD5 511c5ca8ebe618f6a6dca886b58acd08 (389,710,101 bytes)
```

The record also contains `coverage_raw.tar.gz` (3.8 GB), which this study does not use.

## 5. LCBench: learning curves of neural-network configurations

Learning curves of 2,000 hyperparameter configurations of neural networks on each of 35
OpenML datasets; the target is the final validation accuracy and the cost the training time.

- Zimmer, Lindauer, Hutter. *Auto-PyTorch: Multi-Fidelity MetaLearning for Efficient and Robust
  AutoDL.* IEEE TPAMI 43(9), 2021.

The figshare file is a zip archive containing a single file, `data_2k_lw.json`:

```bash
curl -fL --retry 3 -o data/raw/data_2k_lw.zip https://ndownloader.figshare.com/files/21188598
unzip -q data/raw/data_2k_lw.zip -d data/raw    # writes data/raw/data_2k_lw.json (974,453,809 bytes)
rm data/raw/data_2k_lw.zip                      # optional
```

## 6. Linux: TuxKConfig kernel-size pools

Pools of randomly generated kernel configurations for seven releases (v4.13, v4.15, v4.20,
v5.0, v5.4, v5.7, v5.8), with 19,952 to 92,562 configurations per release; the only measured
property is the size of the `vmlinux` image.

- Borges, Pereira, Khelladi, Acher. *Linux Kernel Configurations at Scale: A Dataset for
  Performance and Evolution Analysis.* EASE 2025.

The data is published on OpenML as one dataset per release:

| Release | 4.13 | 4.15 | 4.20 | 5.0 | 5.4 | 5.7 | 5.8 |
|---|---|---|---|---|---|---|---|
| OpenML id | 46759 | 46739 | 46740 | 46741 | 46742 | 46743 | 46744 |

`scripts/convert_tuxkconfig_openml.py` downloads each dataset with the `openml` package and
stores it as `data/raw/linux/tuxkconfig_<release>.parquet`, casting the option columns to
`uint8` (the column names are kept unchanged):

```bash
pip install openml pyarrow
python scripts/convert_tuxkconfig_openml.py --releases 413 415 420 500 504 507 508
```

OpenML returns `float64` columns, so the conversion of the largest release (4.13,
92,562 × 9,488) temporarily needs about 7 GB of memory. On smaller machines, convert one
release per invocation (`--releases 413`, then `--releases 415`, ...).

## Final layout

```
data/raw/
├── fse_artifact/data/sampling/<system>/...           # 1. Kaltenecker
├── AllRuns.zip                                       # 2. x264
├── TwinsOrFalseFriends-ICSE-2023-AE_v1.0.0.zip       # 3. Energy
├── artifact_excluding_raw_coverage.zip               # 4. Workload
├── data_2k_lw.json                                   # 5. LCBench
└── linux/tuxkconfig_{413,415,420,500,504,507,508}.parquet   # 6. Linux
```

## Terms of use

The datasets remain under the terms of their original publications and archives; please cite
the original studies listed above when reusing them. The code of this repository is licensed
separately (see `LICENSE`).
