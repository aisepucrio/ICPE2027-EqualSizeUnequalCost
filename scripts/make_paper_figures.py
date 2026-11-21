#!/usr/bin/env python3
"""Figures 1-8 of the paper, built from the committed artifacts.

  Figure 1  fig_intro_berkeleydb.pdf        posterior risk against cost share, BerkeleyDB samples
  Figure 2  fig_rq1_confidence_7z.pdf       prior and posterior confidence per strategy, 7z
  Figure 3  fig_rq1_discrepancy_small.pdf   confidence discrepancy per system over small risks
  Figure 4  fig_rq1_discrepancy_solver.pdf  confidence discrepancy of plain solver sampling
  Figure 5  fig_rq1_omega_budget.pdf        omega / omega_max against the sample size
  Figure 6  fig_rq2_frontier_anatomy.pdf    size- vs cost-based Pareto frontier (BerkeleyDB, nginx)
  Figure 7  fig_rq2_equal_spend.pdf         pilotCost vs uniform random at equal expenditure
  Figure 8  fig_rq3_srs_budget.pdf          standing of SRS against the sample size

Figures 1-4 are computed from the per-sample posterior risks of the Kaltenecker corpus
(posterior_records.csv) with the confidence functions of `cost_sampling.posterior`.

Usage:
  python scripts/make_paper_figures.py [--artifacts DIR] [--out DIR] [--png]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import to_rgba  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from cost_sampling.posterior import posterior_confidence, prior_confidence  # noqa: E402

# Palette and style of the paper figures.
INK = "#52514e"
GRID = "#e4e3df"
SHADE = "#ecebe7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
GREEN = "#1baf7a"
YELLOW = "#eda100"
PINK = "#e87ba4"
DARKGREEN = "#008300"
PURPLE = "#4a3aa7"
GREYFILL = "#8a8984"

ORACLES = {"cheapOracle", "expensiveOracle"}
SRS_BATCH = 25

DIRS = {
    "Kaltenecker": "fse_posterior_fse_artifact_final_t2",
    "x264": "fse_posterior_x264_icpe_final",
    "Energy": "fse_posterior_energy_final",
    "Workload": "fse_posterior_workload_final",
    "Linux": "fse_posterior_linux_all_full",
    "LCBench": "fse_posterior_lcbench_no_oracles_final",
}
EQUAL_SPEND = {
    "Energy": "fse_posterior_energy_equal_spend/equal_spend_scope_summary.csv",
    "LCBench": "fse_posterior_lcbench_equal_spend/equal_spend_scope_summary.csv",
}
CORPUS_STYLE = {  # marker, colour
    "Kaltenecker": ("o", BLUE),
    "x264": ("D", ORANGE),
    "Energy": ("^", GREEN),
    "Workload": ("s", YELLOW),
    "LCBench": ("v", PINK),
    "Linux": ("P", DARKGREEN),
}
STRATEGY_STYLE = {  # label, marker, colour (legend order)
    "random": ("Uniform random", "o", BLUE),
    "solverBased": ("Solver-based", "s", PURPLE),
    "divDistBased": ("Distance-based", "^", GREEN),
    "twise": ("2-wise", "x", "black"),
    "SRSSampling": ("SRS", "D", ORANGE),
    "balanced": ("Balanced", "P", GREYFILL),
    "diversity": ("Diversity", "h", GREEN),
    "pairwise": ("Pairwise", "X", GREYFILL),
    "pilotCost": ("pilotCost", "v", PURPLE),
}
FRONTIER_SCOPES = [  # corpus, context, level, row label
    ("Kaltenecker", "BerkeleyDBC", "t2", "BerkeleyDB (Kaltenecker)\n$N=97$"),
    ("Energy", "nginx__cost_energy__target_performance", "n32",
     "nginx (Energy; target runtime,\ncost energy), $N=32$"),
]


def set_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 7,
        "axes.labelsize": 7.5,
        "axes.titlesize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 7,
        "axes.edgecolor": INK,
        "axes.linewidth": 0.8,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "pdf.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


def plain(value, _pos=None) -> str:
    return f"{value:g}"


def strategy_summary(artifacts: Path, corpus: str) -> pd.DataFrame:
    s = pd.read_csv(artifacts / DIRS[corpus] / "posterior_strategy_summary.csv")
    return s[~s.strategy.isin(ORACLES)].copy()


# --------------------------------------------------------------------------- equal spend
def fig_equal_spend(artifacts: Path) -> plt.Figure:
    risk, size, labels = [], [], []
    for corpus, path in EQUAL_SPEND.items():
        df = pd.read_csv(artifacts / path)
        defined = df.random_risk > 0
        ratio = df.pilotCost_risk[defined] / df.random_risk[defined]
        print(f"[equal spend] {corpus}: {len(df)} scopes, {int((~defined).sum())} omitted (random risk 0), "
              f"{int((ratio == 0).sum())} with pilotCost risk 0; median risk ratio {ratio.median():.3f}, "
              f"median size ratio {df.pilotCost_n_multiplier.median():.3f}")
        # Scopes where pilotCost attains zero risk enter the box statistics but lie below the log axis.
        risk.append(ratio.to_numpy())
        size.append(df.pilotCost_n_multiplier.to_numpy())
        labels.append(corpus)

    fig, axes = plt.subplots(1, 2, figsize=(4.28, 2.12), gridspec_kw={"wspace": 0.75})
    panels = ((axes[0], risk, "pilotCost / random\nmedian posterior risk", True),
              (axes[1], size, "pilotCost / random\nafforded sample size", False))
    for ax, data, ylabel, log in panels:
        ax.boxplot(
            data, positions=[0, 1], widths=0.5, whis=(5, 95), patch_artist=True,
            boxprops=dict(facecolor=to_rgba(PURPLE, 0.35), edgecolor=to_rgba(PURPLE, 0.6), linewidth=1.0),
            medianprops=dict(color="black", linewidth=1.0),
            whiskerprops=dict(color=INK, linewidth=0.8),
            capprops=dict(color=INK, linewidth=0.8),
            flierprops=dict(marker="o", markersize=2, markerfacecolor=INK, markeredgecolor="none", alpha=0.6),
        )
        ax.axhline(1, color="black", linestyle="--", linewidth=0.8, zorder=1)
        ax.set_xticks([0, 1], labels)
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylabel(ylabel)
        if log:
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(FuncFormatter(plain))
            low, high = ax.get_ylim()  # keep at least one labelled decade on each side of 1
            ax.set_ylim(min(low, 0.08), max(high, 12))
        else:
            ax.set_ylim(bottom=min(0, ax.get_ylim()[0]))
    return fig


# --------------------------------------------------------------------------- frontier anatomy
def pareto_front(points: pd.DataFrame, x: str, y: str) -> list[str]:
    """Strategies not dominated when minimising x and maximising y."""
    ordered = points.sort_values([x, y], ascending=[True, False])
    front, best = [], -np.inf
    for _, row in ordered.iterrows():
        if row[y] > best:
            front.append(row.strategy)
            best = row[y]
    return front


def draw_points(ax, points: pd.DataFrame, x: str, front: list[str]) -> None:
    for strategy, (_, marker, colour) in STRATEGY_STYLE.items():
        row = points[points.strategy == strategy]
        if row.empty:
            continue
        on_front = strategy in front
        kwargs = dict(marker=marker, markersize=7, linestyle="none", zorder=4 if on_front else 3)
        if marker == "x":
            kwargs.update(color=colour, markeredgewidth=1.2)
        elif on_front and colour == GREYFILL:
            kwargs.update(markerfacecolor=colour, markeredgecolor=INK, markeredgewidth=1.0)
        elif on_front:
            kwargs.update(markerfacecolor=colour, markeredgewidth=0)
        else:
            edge = INK if colour == GREYFILL else colour
            kwargs.update(markerfacecolor="white", markeredgecolor=edge, markeredgewidth=1.1)
        ax.plot(row[x], row.y, **kwargs)
    if len(front) > 1:
        fp = points.set_index("strategy").loc[front].sort_values(x)
        ax.plot(fp[x], fp.y, drawstyle="steps-post", linestyle="--", color=INK, linewidth=0.8, zorder=2)


def fig_frontier_anatomy(artifacts: Path) -> plt.Figure:
    fig, axes = plt.subplots(2, 2, figsize=(5.70, 4.07), sharey="row",
                             gridspec_kw={"hspace": 0.32, "wspace": 0.07})
    for r, (corpus, context, level, row_label) in enumerate(FRONTIER_SCOPES):
        s = strategy_summary(artifacts, corpus)
        points = s[(s.context == context) & (s.level == level)].copy()
        points["size"] = 100 * points.pct_n
        points["cost"] = 100 * points.median_pct_cost
        points["y"] = points.posterior_confidence_area
        size_front = pareto_front(points, "size", "y")
        cost_front = pareto_front(points, "cost", "y")
        print(f"[frontier] {context} {level}: size front {size_front}; cost front {cost_front}")
        for strategy in cost_front:
            row = points[points.strategy == strategy].iloc[0]
            print(f"           {strategy:12s} cost {row.cost:.3f}%  A_post {row.y:.3f}")

        ax = axes[r, 0]
        draw_points(ax, points, "size", size_front)
        pct = points["size"].median()
        ax.set_xticks([pct], [f"{pct:.2f}"])
        ax.set_xlim(pct * 0.5, pct * 1.5)
        ax.set_ylabel(r"$A_{\mathrm{post}}$")
        ax.text(-0.33, 0.5, row_label, transform=ax.transAxes, rotation=90, ha="center", va="center",
                fontsize=7.5)

        ax = axes[r, 1]
        draw_points(ax, points, "cost", cost_front)
        ax.tick_params(axis="y", labelleft=False)

    axes[0, 0].set_title("Budget indexed by sample size")
    axes[0, 1].set_title("Budget indexed by measured cost")
    axes[1, 0].set_xlabel("Size share %n (%)")
    axes[1, 1].set_xlabel("Cost share %cost (%)")
    handles = []
    for strategy, (label, marker, colour) in STRATEGY_STYLE.items():
        edge = INK if colour == GREYFILL else colour
        width = 1.2 if marker == "x" else (1.0 if colour == GREYFILL else 0)
        handles.append(Line2D([], [], marker=marker, linestyle="none", markersize=7, label=label,
                              color=colour, markerfacecolor=colour, markeredgecolor=edge,
                              markeredgewidth=width))
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=5, frameon=False,
               handletextpad=0.6, columnspacing=1.6)
    return fig


# --------------------------------------------------------------------------- SRS against budget
def scope_levels(summary: pd.DataFrame, corpus: str) -> pd.DataFrame:
    """One row per (context, level) with its nominal N and the budget tier used on the x axis."""
    nominal = summary[summary.strategy == "random"].groupby(["context", "level"]).n.median()
    df = nominal.rename("N").reset_index()
    if corpus == "Linux":  # levels are named by N; tier = rank of the budget within a release
        df["tier"] = df.groupby("context").N.rank(method="first").astype(int)
    else:
        df["tier"] = df.level
    return df


def srs_shares(artifacts: Path, corpus: str) -> pd.DataFrame:
    s = strategy_summary(artifacts, corpus)
    levels = scope_levels(s, corpus)
    hyp = pd.read_csv(artifacts / DIRS[corpus] / "posterior_hypothesis_tests.csv")
    h2 = hyp[hyp.hypothesis == "FSE5"].copy()
    h2[["context", "level"]] = h2.scope.str.rsplit(":", n=1, expand=True)
    h2 = h2.assign(h2=(h2.verdict == "supports").astype(int))[["context", "level", "h2"]]
    best = s.loc[s.groupby(["context", "level"]).omega_cost_baseline.idxmax(), ["context", "level", "strategy"]]
    best = best.assign(h5=(best.strategy == "SRSSampling").astype(int)).drop(columns="strategy")
    df = levels.merge(h2, on=["context", "level"], how="left").merge(best, on=["context", "level"], how="left")
    df["h2"] = df.h2.fillna(0)
    out = df.groupby("tier").agg(N=("N", "median"), h2=("h2", "mean"), h5=("h5", "mean"),
                                 scopes=("h2", "size")).sort_values("N")
    return out


def fig_srs_budget(artifacts: Path) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(6.45, 2.11), sharex=True, sharey=True,
                             gridspec_kw={"wspace": 0.12})
    shares = {corpus: srs_shares(artifacts, corpus) for corpus in DIRS}
    equal = {}
    for corpus, path in EQUAL_SPEND.items():
        df = pd.read_csv(artifacts / path)
        df["N"] = df.ref_level.str.lstrip("n").astype(int)
        equal[corpus] = df.groupby("N").srs_beats_random.mean().sort_index()

    for corpus, table in shares.items():
        print(f"[srs budget] {corpus}: " + "; ".join(
            f"N={row.N:g}: H2 {row.h2:.3f} H5 {row.h5:.3f} ({row.scopes} scopes)" for row in table.itertuples()))
    for corpus, series in equal.items():
        print(f"[srs budget] {corpus} equal spend: " + "; ".join(f"N={n}: {v:.3f}" for n, v in series.items()))

    def line(ax, corpus, x, y):
        marker, colour = CORPUS_STYLE[corpus]
        ax.plot(x, y, marker=marker, color=colour, linewidth=1.3, markersize=4.5,
                markeredgecolor="white", markeredgewidth=0.5,
                linestyle="none" if len(x) == 1 else "-", zorder=3)

    for ax, key, title in ((axes[0], "h2", "H2 (fixed sample size)"), (axes[1], "h5", "H5 (cost index)")):
        for corpus, table in shares.items():
            line(ax, corpus, table.N.to_numpy(), table[key].to_numpy())
        ax.set_title(title)
    for corpus, series in equal.items():
        line(axes[2], corpus, series.index.to_numpy(), series.to_numpy())
    axes[2].set_title("Equal expenditure")

    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlim(6, 2800)
        ax.axvspan(1, SRS_BATCH, color=SHADE, linewidth=0, zorder=0)
        ax.xaxis.set_major_locator(FixedLocator([10, 100, 1000]))
        ax.xaxis.set_major_formatter(FuncFormatter(plain))
        ax.xaxis.set_minor_locator(FixedLocator([]))
        ax.set_xlabel("Sample size $N$")
        ax.set_ylim(-0.03, 1.03)
        ax.set_yticks(np.linspace(0, 1, 6))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}"))
    axes[0].set_ylabel("Share of scopes")
    handles = []
    for corpus, (marker, colour) in CORPUS_STYLE.items():
        handles.append(Line2D([], [], marker=marker, color=colour, linewidth=1.3, markersize=4.5,
                              markeredgecolor="white", markeredgewidth=0.5,
                              linestyle="none" if corpus == "Kaltenecker" else "-", label=corpus))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=6, frameon=False,
               columnspacing=1.4, handlelength=2.0)
    return fig


# --------------------------------------------------------------------------- Figures 1-5
KALTENECKER_SYSTEMS = ["7z", "BerkeleyDBC", "Dune", "Hipacc", "JavaGC", "LLVM", "Polly"]
SYSTEM_LABELS = {"BerkeleyDBC": "BerkeleyDB", "Hipacc": "HIPAcc"}
RQ1_STRATEGIES = [("random", "Uniform random", BLUE), ("divDistBased", "Distance-based", GREEN),
                  ("solverBased", "Solver-based", PURPLE), ("SRSSampling", "SRS", ORANGE)]


def minus(value, _pos=None) -> str:
    return f"{value:.1f}".replace("-", "−")


def kaltenecker_records(artifacts: Path) -> pd.DataFrame:
    return pd.read_csv(artifacts / DIRS["Kaltenecker"] / "posterior_records.csv")


def confidence_curves(records: pd.DataFrame, context: str, strategy: str, eps: np.ndarray):
    """Posterior and prior confidence as in the pipeline: the prior uses the median sample size
    of the strategy's samples and the artifact-compatible exponent N + 1."""
    rows = records[(records.context == context) & (records.strategy == strategy)]
    risks = rows.posterior_risk.to_numpy()
    n = float(np.median(rows.n))
    return posterior_confidence(eps, risks), prior_confidence(eps, n, exponent_offset=1), risks


def two_wise(records: pd.DataFrame, context: str) -> tuple[float, int]:
    """Posterior risk of the deterministic 2-wise sample and the nominal sample size N_2-wise
    (the size of the uniform random samples; de-duplication can shorten other samples)."""
    rows = records[(records.context == context) & (records.strategy == "twise")]
    random = records[(records.context == context) & (records.strategy == "random")]
    return float(rows.posterior_risk.median()), int(np.median(random.n))


def curve_end(risks: np.ndarray, n: float, tolerance: float = 1e-3) -> float:
    """Risk up to which a discrepancy curve is drawn: past the largest observed risk, until the
    prior confidence reaches 1 - tolerance (beyond it, |eta| < tolerance)."""
    return max(float(risks.max()), 1.0 - tolerance ** (1.0 / (n + 1.0)))


def fig_intro_berkeleydb(artifacts: Path) -> plt.Figure:
    """Figure 1: posterior risk against cost share of every BerkeleyDB sample at N = N_2-wise."""
    rec = kaltenecker_records(artifacts)
    rec = rec[rec.context == "BerkeleyDBC"].assign(cost=lambda d: 100 * d.pct_cost,
                                                   risk=lambda d: 100 * d.posterior_risk)
    size_share = 100 * float(rec.pct_n.median())
    n = int(rec[rec.strategy == "random"].n.median())
    style = {"axes.edgecolor": "black", "xtick.color": "black", "ytick.color": "black",
             "axes.grid.axis": "both", "xtick.labelsize": 7.5, "ytick.labelsize": 7.5}
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(3.35, 2.45))
        fig.subplots_adjust(left=0.135, right=0.985, bottom=0.165, top=0.83)
        order = [("solverBased", "Solver-based", "s"), ("divDistBased", "Distance-based", "^"),
                 ("random", "Uniform random", "o"), ("SRSSampling", "SRS", "D")]
        colours = {key: STRATEGY_STYLE[key][2] for key, _, _ in order}
        handles = {}
        for key, label, marker in order:
            d = rec[rec.strategy == key]
            ax.scatter(d.cost, d.risk, s=9, marker=marker, color=colours[key], alpha=0.6,
                       edgecolors="white", linewidths=0.3, zorder=3)
            handles[key] = Line2D([], [], marker=marker, linestyle="none", markersize=3.2, color=colours[key],
                                  alpha=0.6, label=label)
        tw = rec[rec.strategy == "twise"].iloc[0]
        ax.scatter([tw.cost], [tw.risk], s=42, marker="X", color="black", edgecolors="white", linewidths=0.4,
                   zorder=4)
        handles["twise"] = Line2D([], [], marker="X", linestyle="none", markersize=6, color="black", label="2-wise")
        ax.axvline(size_share, color="#333333", linestyle="--", linewidth=0.8, zorder=2)
        ax.text(size_share * 1.06, 52, f"size share ({size_share:.1f}%):\nevery sample has\n{n} configurations",
                fontsize=6, va="top", ha="left", color="#222222")
        ax.text(0.52, 2.3, "2-wise: deterministic,\nalways the same sample", fontsize=6, va="top", ha="left",
                color="#222222")
        ax.annotate("", xy=(0.52, 0.042), xytext=(size_share * 0.95, 0.042),
                    arrowprops=dict(arrowstyle="->", color=INK, linewidth=0.6))
        ax.text(0.58, 0.05, "cheaper than its size", fontsize=6, va="bottom", ha="left", color=INK)
        ax.set_xscale("log", base=2)
        ax.set_xlim(0.44, 20)
        ax.xaxis.set_major_locator(FixedLocator([0.5, 1, 2, 4, 8, 16]))
        ax.xaxis.set_major_formatter(FuncFormatter(plain))
        ax.xaxis.set_minor_locator(FixedLocator([]))
        ax.set_yscale("symlog", linthresh=0.1, linscale=0.625)
        ax.set_ylim(-0.012, 80)
        ax.yaxis.set_major_locator(FixedLocator([0, 0.1, 1, 10, 50]))
        ax.yaxis.set_major_formatter(FuncFormatter(plain))
        ax.yaxis.set_minor_locator(FixedLocator([]))
        ax.grid(color=GRID, linewidth=0.35)
        ax.set_xlabel("Cost share of the sample (% of total cost)")
        ax.set_ylabel("Posterior risk (%)")
        legend_order = ["solverBased", "twise", "divDistBased", "random", "SRSSampling"]
        fig.legend(handles=[handles[k] for k in legend_order], loc="upper center", bbox_to_anchor=(0.56, 1.0),
                   ncol=3, frameon=False, fontsize=6, handletextpad=0.4, columnspacing=1.4)
    fig.fixed_size = True
    return fig


def fig_confidence_7z(artifacts: Path) -> plt.Figure:
    """Figure 2: prior and posterior confidence per strategy for 7z at N = N_2-wise."""
    rec = kaltenecker_records(artifacts)
    eps = np.linspace(0.0, 0.008, 4001)
    fig, axes = plt.subplots(1, 4, figsize=(6.31, 1.28), sharey=True, gridspec_kw={"wspace": 0.25})
    for ax, (key, label, colour) in zip(axes, RQ1_STRATEGIES):
        post, prior, _ = confidence_curves(rec, "7z", key, eps)
        ax.fill_between(eps, post, step="post", color=colour, alpha=0.28, linewidth=0)
        ax.plot(eps, post, drawstyle="steps-post", color=colour, linewidth=1.2, label=r"posterior $\hat{\gamma}$")
        ax.plot(eps, prior, color="black", linestyle="--", linewidth=1.0, label=r"prior $\gamma$")
        ax.set_title(label)
        ax.set_xlim(0, 0.008)
        ax.set_ylim(0, 1.01)
        ax.set_xticks([0, 0.004, 0.008], ["0", "0.004", "0.008"])
        ax.set_yticks([0, 0.5, 1.0])
        ax.yaxis.set_major_formatter(FuncFormatter(minus))
        ax.set_xlabel(r"Risk $\varepsilon$")
    axes[0].set_ylabel("Confidence")
    axes[0].legend(loc="lower right", bbox_to_anchor=(1.0, 0.08), frameon=False, fontsize=7, handlelength=2.0)
    return fig


def fig_discrepancy_small(artifacts: Path) -> plt.Figure:
    """Figure 3: confidence discrepancy per system and strategy over small risks."""
    rec = kaltenecker_records(artifacts)
    eps = np.logspace(-4, -1, 3000)
    fig, axes = plt.subplots(2, 4, figsize=(6.0, 2.94), sharey=True, gridspec_kw={"hspace": 0.62, "wspace": 0.26})
    flat = axes.ravel()
    for i, (ax, ctx) in enumerate(zip(flat, KALTENECKER_SYSTEMS)):
        risk_2wise, n = two_wise(rec, ctx)
        ax.axhline(0, color=INK, linewidth=0.8, zorder=1)
        for key, _, colour in RQ1_STRATEGIES:
            post, prior, risks = confidence_curves(rec, ctx, key, eps)
            n_strategy = float(np.median(rec[(rec.context == ctx) & (rec.strategy == key)].n))
            keep = eps <= curve_end(risks, n_strategy)
            ax.plot(eps[keep], (post - prior)[keep], color=colour, linewidth=1.1, drawstyle="steps-post", zorder=3)
        ax.axvline(risk_2wise, color="black", linestyle=":", linewidth=0.8, zorder=2)
        ax.set_xscale("log")
        ax.set_xlim(1e-4, 1e-1)
        ax.set_ylim(-1.0, 1.0)
        ax.set_yticks([-1, -0.5, 0, 0.5, 1])
        ax.yaxis.set_major_formatter(FuncFormatter(minus))
        ax.xaxis.set_major_locator(FixedLocator([1e-4, 1e-3, 1e-2, 1e-1]))
        ax.xaxis.set_minor_locator(FixedLocator([]))
        ax.set_title(f"{SYSTEM_LABELS.get(ctx, ctx)}, $N$={n}")
        bottom = i >= 4 or i == 3
        ax.tick_params(axis="x", labelbottom=bottom)
        if bottom:
            ax.set_xlabel(r"Risk $\varepsilon$")
        if i % 4 == 0:
            ax.set_ylabel(r"$\eta=\hat{\gamma}-\gamma$")
    legend_ax = flat[7]
    legend_ax.axis("off")
    handles = [Line2D([], [], color=c, linewidth=1.1, label=l) for _, l, c in RQ1_STRATEGIES]
    handles.append(Line2D([], [], color="black", linestyle=":", linewidth=0.8,
                          label=r"$\hat{\varepsilon}_{\mathrm{2\text{-}wise}}$"))
    legend_ax.legend(handles=handles, loc="center left", frameon=False, fontsize=7, handlelength=2.0)
    return fig


def fig_discrepancy_solver(artifacts: Path) -> plt.Figure:
    """Figure 4: confidence discrepancy of plain solver sampling over the risk range [0, 0.65]."""
    rec = kaltenecker_records(artifacts)
    eps = np.linspace(0.0, 0.65, 6501)
    fig, axes = plt.subplots(1, 7, figsize=(6.3, 1.06), sharey=True, gridspec_kw={"wspace": 0.25})
    for ax, ctx in zip(axes, KALTENECKER_SYSTEMS):
        post, prior, _ = confidence_curves(rec, ctx, "solverBased", eps)
        ax.axhline(0, color=INK, linewidth=0.8, zorder=1)
        ax.plot(eps, post - prior, color=PURPLE, linewidth=1.1, drawstyle="steps-post", zorder=3)
        ax.set_title(SYSTEM_LABELS.get(ctx, ctx))
        ax.set_xlim(0, 0.65)
        ax.set_ylim(-1.0, 1.0)
        ax.set_xticks([0, 0.3, 0.6])
        ax.xaxis.set_major_formatter(FuncFormatter(minus))
        ax.set_yticks([-1, 0, 1])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}".replace("-", "−")))
    axes[0].set_ylabel(r"$\eta$ (solver-based)")
    fig.supxlabel(r"Risk $\varepsilon$", fontsize=7.5, y=-0.2)
    return fig


def fig_omega_budget(artifacts: Path) -> plt.Figure:
    """Figure 5: omega / omega_max against the sample size, median over the contexts of a corpus."""
    panels = [("SRSSampling", "SRS"), ("random", "Uniform random"), ("diversity", "Distance-based / Diversity")]
    fig, axes = plt.subplots(1, 3, figsize=(6.33, 2.11), sharex=True, sharey=True, gridspec_kw={"wspace": 0.12})
    for ax, (key, title) in zip(axes, panels):
        for corpus in DIRS:
            s = strategy_summary(artifacts, corpus)
            levels = scope_levels(s, corpus)
            strategy = "divDistBased" if key == "diversity" and corpus in ("Kaltenecker", "x264") else key
            rows = s[s.strategy == strategy].merge(levels, on=["context", "level"])
            table = rows.groupby("tier").agg(N=("N", "median"), omega=("omega_size_over_max", "median")).sort_values("N")
            marker, colour = CORPUS_STYLE[corpus]
            ax.plot(table.N, table.omega, marker=marker, color=colour, linewidth=1.3, markersize=4.5,
                    markeredgecolor="white", markeredgewidth=0.5, linestyle="none" if len(table) == 1 else "-",
                    zorder=3)
        ax.axhline(0, color=INK, linewidth=0.8, zorder=1)
        ax.set_title(title)
        ax.set_xscale("log")
        ax.set_xlim(6, 2800)
        ax.axvspan(1, SRS_BATCH, color=SHADE, linewidth=0, zorder=0)
        ax.xaxis.set_major_locator(FixedLocator([10, 100, 1000]))
        ax.xaxis.set_major_formatter(FuncFormatter(plain))
        ax.xaxis.set_minor_locator(FixedLocator([]))
        ax.set_xlabel("Sample size $N$")
        ax.set_ylim(-1.05, 1.05)
        ax.set_yticks([-1, -0.5, 0, 0.5, 1])
        ax.yaxis.set_major_formatter(FuncFormatter(minus))
    axes[0].set_ylabel(r"$\omega/\omega_{\max}$ (median over contexts)")
    handles = [Line2D([], [], marker=m, color=c, linewidth=1.3, markersize=4.5, markeredgecolor="white",
                      markeredgewidth=0.5, linestyle="none" if corpus == "Kaltenecker" else "-", label=corpus)
               for corpus, (m, c) in CORPUS_STYLE.items()]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=6, frameon=False,
               columnspacing=1.4, handlelength=2.0)
    return fig


FIGURES = {  # file name (as in the paper sources): builder
    "fig_intro_berkeleydb": fig_intro_berkeleydb,          # Figure 1
    "fig_rq1_confidence_7z": fig_confidence_7z,            # Figure 2
    "fig_rq1_discrepancy_small": fig_discrepancy_small,    # Figure 3
    "fig_rq1_discrepancy_solver": fig_discrepancy_solver,  # Figure 4
    "fig_rq1_omega_budget": fig_omega_budget,              # Figure 5
    "fig_rq2_frontier_anatomy": fig_frontier_anatomy,      # Figure 6
    "fig_rq2_equal_spend": fig_equal_spend,                # Figure 7
    "fig_rq3_srs_budget": fig_srs_budget,                  # Figure 8
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--artifacts", type=Path, default=REPO / "artifacts")
    parser.add_argument("--out", type=Path, default=REPO / "artifacts" / "paper_figures")
    parser.add_argument("--png", action="store_true", help="also write 300 dpi PNG previews")
    args = parser.parse_args()
    set_style()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, build in FIGURES.items():
        fig = build(args.artifacts)
        bbox = fig.bbox_inches if getattr(fig, "fixed_size", False) else "tight"  # Figure 1 keeps its exact size
        fig.savefig(args.out / f"{name}.pdf", metadata={"CreationDate": None}, bbox_inches=bbox)
        if args.png:
            fig.savefig(args.out / f"{name}.png", dpi=300, bbox_inches=bbox)
        plt.close(fig)
        print(f"wrote {args.out / name}.pdf")


if __name__ == "__main__":
    main()
