#!/usr/bin/env python3
"""Tables 3-7 of the paper, computed from the committed per-corpus results.

Definitions (as in the paper):
  scope   one (context, budget level) cell; x264 at t2, the Kaltenecker corpus at N_2-wise.
  H1      posterior-risk distributions differ across strategies (Kruskal-Wallis; FSE1 tests)
  H2      SRS has lower posterior risk than uniform random sampling (FSE5 tests)
  H3      SRS and uniform random sampling differ in measured cost (FSE6 tests)
  H4      the top recommendation changes: the strategy with the largest omega against the
          size-based baseline differs from the one with the largest omega against the
          cost-based baseline
  H5      SRS is the top recommendation at equal cost
  H6      the Pareto frontier of guarantee and budget changes (Jaccard overlap of the size-based
          and the cost-based frontier below 1), computed with the pipeline's own frontier rule
Benjamini-Hochberg correction (FDR 0.05) is applied within each (corpus, hypothesis) family
over all conducted tests, as in scripts/mcc_sensitivity.py. Diagnostic oracle strategies are
excluded everywhere.

Writes artifacts/paper_tables/paper_tables.md and one CSV per table.

Usage: python scripts/make_paper_tables.py [--artifacts DIR] [--out DIR]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from run_fse_posterior import level_confidence_frontiers  # noqa: E402

ALPHA = 0.05
ORACLES = {"cheapOracle", "expensiveOracle"}
CORPORA = {
    "Kaltenecker": "fse_posterior_fse_artifact_final_t2",
    "x264": "fse_posterior_x264_icpe_final",
    "Energy": "fse_posterior_energy_final",
    "Workload": "fse_posterior_workload_final",
    "Linux": "fse_posterior_linux_all_full",
    "LCBench": "fse_posterior_lcbench_no_oracles_final",
}
COUPLING = {"Kaltenecker": "id.", "x264": "id./asym.", "Energy": "id./asym.", "Workload": "id.",
            "Linux": "id.", "LCBench": "weak"}
SYSTEM_NAMES = {"BerkeleyDBC": "BerkeleyDB", "Hipacc": "HIPAcc"}
OMEGA_STRATEGIES = [("random", "Uniform random"), ("divDistBased", "Distance-based"),
                    ("solverBased", "Solver-based"), ("twise", "2-wise"), ("SRSSampling", "SRS")]


def level_key(level) -> float:
    digits = "".join(ch for ch in str(level) if ch.isdigit())
    return float(digits) if digits else 0.0


def bh_qvalues(p: np.ndarray) -> np.ndarray:
    m = len(p)
    order = np.argsort(p)
    ranked = p[order] * m / (np.arange(m) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(q, 1.0)
    return out


class Corpus:
    def __init__(self, artifacts: Path, name: str):
        self.name = name
        self.dir = artifacts / CORPORA[name]
        s = pd.read_csv(self.dir / "posterior_strategy_summary.csv")
        self.all_levels = s[~s.strategy.isin(ORACLES)].copy()
        self.summary = self.all_levels[self.all_levels.level == "t2"] if name == "x264" else self.all_levels
        tests = pd.read_csv(self.dir / "posterior_hypothesis_tests.csv")
        parts = tests.scope.str.rsplit(":", n=1, expand=True)
        tests["context"], tests["level"] = parts[0], parts[1]
        tests["bh_supports"] = False
        for hyp in ("FSE1", "FSE5", "FSE6"):
            fam = tests[(tests.hypothesis == hyp) & tests.p_value.notna()]
            q = bh_qvalues(fam.p_value.to_numpy())
            tests.loc[fam.index, "bh_supports"] = (fam.verdict == "supports").to_numpy() & (q <= ALPHA)
        self.tests = tests[tests.level == "t2"] if name == "x264" else tests
        self.decisions = self._decisions()

    def _decisions(self) -> pd.DataFrame:
        rows = []
        for (ctx, lv), g in self.summary.groupby(["context", "level"]):
            best_size = g.loc[g.omega_size_baseline.idxmax(), "strategy"]
            best_cost = g.loc[g.omega_cost_baseline.idxmax(), "strategy"]
            r = g.median_calibration_ratio
            size_front, cost_front = level_confidence_frontiers(g.to_dict("records"))
            union = size_front | cost_front
            jaccard = len(size_front & cost_front) / len(union) if union else 1.0
            rows.append({"context": ctx, "level": lv, "h4": best_size != best_cost,
                         "h5": best_cost == "SRSSampling", "h6": jaccard < 1.0,
                         "srs_on_front": f"SRSSampling_{lv}" in cost_front, "jaccard": jaccard,
                         "spread": r.max() / r.min()})
        return pd.DataFrame(rows)

    @property
    def scopes(self) -> int:
        return len(self.decisions)

    def supports(self, hyp: str) -> tuple[int, int]:
        t = self.tests[self.tests.hypothesis == hyp]
        return int((t.verdict == "supports").sum()), int(t.bh_supports.sum())

    def mean_rank(self, strategy: str) -> str:
        s = self.summary.copy()
        if strategy not in set(s.strategy):
            return "--"
        s["rank"] = s.groupby(["context", "level"]).median_posterior_risk.rank(method="average")
        return f"{s[s.strategy == strategy]['rank'].mean():.1f}/{s.strategy.nunique()}"

    def monotone(self, strategy: str | None = None) -> str:
        s = self.all_levels
        if s.level.nunique() == 1:
            return "--"
        flags = []
        for (_, st), g in s.groupby(["context", "strategy"]):
            if strategy and st != strategy:
                continue
            g = g.sort_values("level", key=lambda x: x.map(level_key))
            flags.append(bool(np.all(np.diff(g.median_posterior_risk.to_numpy()) <= 1e-12)))
        return f"{100 * np.mean(flags):.0f}%"


def count(raw: int, bh: int) -> str:
    return f"{raw}" if raw == bh else f"{raw} ({bh})"


def pct(k: int, n: int) -> str:
    return f"{100 * k / n:.0f}%"


def markdown(df: pd.DataFrame) -> list[str]:
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--artifacts", type=Path, default=REPO / "artifacts")
    parser.add_argument("--out", type=Path, default=REPO / "artifacts" / "paper_tables")
    args = parser.parse_args()
    corpora = {name: Corpus(args.artifacts, name) for name in CORPORA}
    tables: dict[str, tuple[str, pd.DataFrame]] = {}

    # Table 3: omega / omega_max at N_2-wise for the seven systems of Weis et al.
    k = corpora["Kaltenecker"].summary
    t3 = []
    for ctx in sorted(k.context.unique(), key=str.lower):
        row = {"System": SYSTEM_NAMES.get(ctx, ctx)}
        for key, label in OMEGA_STRATEGIES:
            v = float(k[(k.context == ctx) & (k.strategy == key)].omega_size_over_max.iloc[0])
            row[label] = f"{v:+.3f}".replace("-0.000", "+0.000")
        t3.append(row)
    tables["table3_omega_t2"] = ("Table 3: omega / omega_max at N = N_2-wise (Kaltenecker corpus)", pd.DataFrame(t3))

    # Table 4: RQ1 outcomes per corpus at a fixed sample size.
    t4 = []
    for name, c in corpora.items():
        t4.append({"Corpus": name, "Scopes": c.scopes, "H1 risk differs": count(*c.supports("FSE1")),
                   "H2 SRS < random": count(*c.supports("FSE5")), "Mean rank SRS": c.mean_rank("SRSSampling"),
                   "Mean rank Solver": c.mean_rank("solverBased"), "Monotone all": c.monotone(),
                   "Monotone SRS": c.monotone("SRSSampling")})
    tables["table4_rq1"] = ("Table 4: RQ1 outcomes per corpus at a fixed sample size", pd.DataFrame(t4))

    # Table 5: decisions at equal size and at equal cost.
    t5, jaccards = [], []
    for name, c in corpora.items():
        d = c.decisions
        jaccards.append(d.jaccard)
        h3 = c.supports("FSE6")
        t5.append({"Corpus": name, "Scopes": c.scopes, "H3 cost differs": count(*h3),
                   "H4 top changes": int(d.h4.sum()), "H5 SRS best": int(d.h5.sum()),
                   "H6 frontier changes": int(d.h6.sum()), "SRS on fr.": int(d.srs_on_front.sum()),
                   "Jacc.": f"{d.jaccard.median():.2f}", "_h3": h3[0]})
    t5df = pd.DataFrame(t5)
    total = {"Corpus": "Total", "Scopes": int(t5df.Scopes.sum()), "H3 cost differs": str(int(t5df._h3.sum())),
             "H4 top changes": int(t5df["H4 top changes"].sum()), "H5 SRS best": int(t5df["H5 SRS best"].sum()),
             "H6 frontier changes": int(t5df["H6 frontier changes"].sum()), "SRS on fr.": int(t5df["SRS on fr."].sum()),
             "Jacc.": f"{pd.concat(jaccards).median():.2f}", "_h3": 0}
    t5df = pd.concat([t5df, pd.DataFrame([total])], ignore_index=True).drop(columns="_h3")
    tables["table5_decisions"] = ("Table 5: decisions at equal size and at equal cost", t5df)

    # Table 6: characteristics of the corpora and decision outcomes.
    t6 = []
    for name, c in corpora.items():
        n = c.all_levels[c.all_levels.strategy == "random"].n
        r = c.summary.median_calibration_ratio
        t6.append({"Corpus": name, "Coupling": COUPLING[name], "Budget N": f"{int(n.min())}-{int(n.max())}",
                   "r p10-p90": f"{r.quantile(0.1):.2f}-{r.quantile(0.9):.2f}",
                   "H2": pct(c.supports("FSE5")[0], c.scopes), "H4": pct(int(c.decisions.h4.sum()), c.scopes),
                   "H5": pct(int(c.decisions.h5.sum()), c.scopes)})
    tables["table6_conditions"] = ("Table 6: characteristics of the corpora and decision outcomes", pd.DataFrame(t6))

    # Table 7: H4 by tercile of the within-scope spread of cost bias r_max / r_min.
    allsc = pd.concat([c.decisions.assign(corpus=name) for name, c in corpora.items()], ignore_index=True)
    allsc["tercile"] = pd.qcut(allsc.spread, 3, labels=["Low", "Middle", "High"])
    t7 = []
    for t, g in allsc.groupby("tercile", observed=True):
        t7.append({"Tercile": t, "Range": f"{g.spread.min():.2f}-{g.spread.max():.2f}", "Scopes": len(g),
                   "H4 top changes": f"{int(g.h4.sum())} ({100 * g.h4.mean():.0f}%)"})
    tables["table7_spread"] = ("Table 7: H4 by tercile of the spread of cost bias r_max / r_min", pd.DataFrame(t7))

    n_scopes = sum(c.scopes for c in corpora.values())
    h1 = sum(c.supports("FSE1")[0] for c in corpora.values())
    h4 = sum(int(c.decisions.h4.sum()) for c in corpora.values())
    h6 = sum(int(c.decisions.h6.sum()) for c in corpora.values())
    differ = more_expensive = 0
    for c in corpora.values():
        t = c.tests[(c.tests.hypothesis == "FSE6") & (c.tests.verdict == "supports")]
        cost = c.summary.set_index(["context", "level", "strategy"]).median_pct_cost
        for row in t.itertuples():
            differ += 1
            more_expensive += int(cost[(row.context, row.level, "SRSSampling")] > cost[(row.context, row.level, "random")])
    text = [
        f"- H1 over all corpora: {h1} of {n_scopes} scopes ({100 * h1 / n_scopes:.1f}%).",
        f"- SRS is the more expensive strategy in {more_expensive} of the {differ} scopes in which its cost "
        f"differs from that of uniform random sampling (H3).",
        f"- H4 over all corpora: {h4} of {n_scopes} scopes ({100 * h4 / n_scopes:.1f}%); "
        f"H6: {h6} of {n_scopes} ({100 * h6 / n_scopes:.1f}%).",
    ]

    rho, p = spearmanr(allsc.spread, allsc.h4.astype(int))
    edge = round(float(allsc[allsc.tercile == "Low"].spread.max()), 2)
    low, high = allsc[allsc.spread <= edge], allsc[allsc.spread > edge]
    notes = [
        f"- Spearman's rho between spread and H4 over all {len(allsc)} scopes: {rho:.2f} (p = {p:.1e}).",
        f"- r_max / r_min <= {edge}: the top recommendation changes in {100 * low.h4.mean():.0f}% of the scopes; "
        f"otherwise in {100 * high.h4.mean():.0f}%.",
    ]
    for name in ("Energy", "Workload"):
        d = corpora[name].decisions
        notes.append(f"- {name}: median spread {d[d.h4].spread.median():.2f} where the top recommendation changes, "
                     f"{d[~d.h4].spread.median():.2f} elsewhere.")

    args.out.mkdir(parents=True, exist_ok=True)
    lines = ["# Paper tables", "", "Generated by `scripts/make_paper_tables.py` from the committed results.",
             "Counts in parentheses are Benjamini-Hochberg-corrected where they differ.", ""]
    for stem, (title, df) in tables.items():
        df.to_csv(args.out / f"{stem}.csv", index=False)
        lines += [f"## {title}", ""] + markdown(df) + [""]
    lines += ["## Numbers quoted in the text", "", "RQ1 and RQ2:", ""] + text + ["", "RQ3:", ""] + notes + [""]
    (args.out / "paper_tables.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
