#!/usr/bin/env python3
"""Paper figures built from the committed artifacts.

Builds, from the committed artifacts:
  fig_rq2_equal_spend.pdf       pilotCost vs uniform random at equal measured spend
  fig_rq2_frontier_anatomy.pdf  size- vs cost-indexed Pareto frontier (BerkeleyDB, nginx)
  fig_rq3_srs_budget.pdf        standing of SRS against the sample size (H2, H5, equal spend)

The figure numbers refer to the paper: Figure 6 (frontier anatomy), Figure 7 (equal
expenditure) and Figure 8 (standing of SRS against the sample size).

Usage:
  python scripts/make_paper_figures.py [--artifacts DIR] [--out DIR] [--png]
"""
from __future__ import annotations

import argparse
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


FIGURES = {
    "fig_rq2_equal_spend": fig_equal_spend,
    "fig_rq2_frontier_anatomy": fig_frontier_anatomy,
    "fig_rq3_srs_budget": fig_srs_budget,
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
        fig.savefig(args.out / f"{name}.pdf", metadata={"CreationDate": None})
        if args.png:
            fig.savefig(args.out / f"{name}.png", dpi=300)
        plt.close(fig)
        print(f"wrote {args.out / name}.pdf")


if __name__ == "__main__":
    main()
