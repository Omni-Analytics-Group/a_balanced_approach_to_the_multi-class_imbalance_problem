# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""Build every static figure in figures/ (light and dark variants).

Run from the repository root:

    uv run scripts/build_figures.py

The citation figures read data/citations.csv. The metric figures are computed
from src/cba.py, so they stay in step with the reference implementation.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cba import (
    accuracy,
    balanced_accuracy,
    class_balance_accuracy,
    macro_precision,
)

FIGURES = ROOT / "figures"
CITATIONS = ROOT / "data" / "citations.csv"
SCHOLAR_COUNT = 167
SKLEARN_RELEASE_YEAR = 2018

THEMES = {
    "light": {
        "surface": "#fcfcfb",
        "ink": "#0b0b0b",
        "ink2": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "neutral": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    },
    "dark": {
        "surface": "#1a1a19",
        "ink": "#f0efec",
        "ink2": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "neutral": "#52514e",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
    },
}

# How a citing work uses the dissertation, folded into four groups for color.
USAGE_GROUPS = {
    "Uses CBA as a metric": "Class Balance Accuracy itself",
    "Builds on CBA": "Class Balance Accuracy itself",
    "Discusses CBA": "Class Balance Accuracy itself",
    "Software": "Class Balance Accuracy itself",
    "Cites it for balanced accuracy": "Balanced accuracy and macro metrics",
    "Cites it for the imbalance problem": "Imbalance background and methods",
    "Cites it for a method": "Imbalance background and methods",
    "Other": "Other or not determined",
    "Not determined": "Other or not determined",
}
GROUP_ORDER = [
    "Class Balance Accuracy itself",
    "Balanced accuracy and macro metrics",
    "Imbalance background and methods",
    "Other or not determined",
]


def usage_group(label: str) -> str:
    """Color group for a usage label. Labels added to the CSV later fall into the last group."""
    return USAGE_GROUPS.get(label, GROUP_ORDER[-1])


def group_colors(theme: dict) -> dict[str, str]:
    series = theme["series"]
    return dict(zip(GROUP_ORDER, [series[0], series[1], series[2], theme["neutral"]]))


def style_axes(ax, theme: dict, *, grid_axis: str | None = "y") -> None:
    ax.set_facecolor(theme["surface"])
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=theme["muted"], length=0, labelsize=10)
    if grid_axis:
        ax.grid(axis=grid_axis, color=theme["grid"], linewidth=1)
        ax.set_axisbelow(True)


def new_figure(theme: dict, width: float, height: float, **kwargs):
    fig, axes = plt.subplots(figsize=(width, height), facecolor=theme["surface"], **kwargs)
    return fig, axes


def titles(fig, theme: dict, title: str, subtitle: str, *, top: float = 0.965) -> None:
    fig.text(0.03, top, title, fontsize=15, fontweight="bold", color=theme["ink"], ha="left", va="top")
    fig.text(0.03, top - 0.062, subtitle, fontsize=10.5, color=theme["ink2"], ha="left", va="top")


def save(fig, name: str, mode: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / f"{name}-{mode}.png"
    fig.savefig(path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------
# Figure 1. Two models, one accuracy (the dissertation's Figure 3.1, recomputed)
# --------------------------------------------------------------------------

BANDS = [  # (x from, x to, majority count, class B count, class C count)
    (0, 25, 500, 500, 0),
    (25, 50, 500, 100, 0),
    (50, 75, 500, 0, 100),
    (75, 100, 500, 0, 500),
]
ALL_MAJORITY = [[2000, 0, 0], [600, 0, 0], [600, 0, 0]]
PARTITIONED = [[1000, 500, 500], [100, 500, 0], [100, 0, 500]]


def band_points(rng: np.random.Generator):
    xs, ys, labels = [], [], []
    for start, stop, *counts in BANDS:
        for label, count in enumerate(counts):
            xs.append(rng.uniform(start, stop, count))
            ys.append(rng.uniform(0, 100, count))
            labels.append(np.full(count, label))
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(labels)


def figure_same_accuracy(mode: str) -> None:
    theme = THEMES[mode]
    colors = theme["series"][:3]
    names = ["Majority class (2,000)", "Minority class B (600)", "Minority class C (600)"]
    rng = np.random.default_rng(2013)
    x, y, label = band_points(rng)
    order = rng.permutation(len(x))

    fig = plt.figure(figsize=(11, 6.6), facecolor=theme["surface"])
    grid = fig.add_gridspec(1, 3, left=0.04, right=0.97, top=0.765, bottom=0.42, wspace=0.12)
    lower = fig.add_gridspec(1, 3, width_ratios=[1.05, 1, 1], left=0.04, right=0.955, top=0.30, bottom=0.07, wspace=0.78)
    titles(
        fig,
        theme,
        "Two models, one accuracy score",
        "Both models get 62.5% of 3,200 observations right. Only one of them can tell the classes apart.",
    )

    panels = [
        ("The data", None),
        ("Model 1: call everything the majority class", [0, 0, 0, 0]),
        ("Model 2: one region per class", [1, 0, 0, 2]),
    ]
    for column, (heading, regions) in enumerate(panels):
        ax = fig.add_subplot(grid[0, column])
        style_axes(ax, theme, grid_axis=None)
        if regions is not None:
            for (start, stop, *_), region in zip(BANDS, regions):
                ax.axvspan(start, stop, color=colors[region], alpha=0.16, linewidth=0)
            for (start, *_), region, previous in zip(BANDS[1:], regions[1:], regions[:-1]):
                if region != previous:
                    ax.axvline(start, color=theme["ink2"], linewidth=1)
        ax.scatter(x[order], y[order], s=3.2, c=[colors[int(i)] for i in label[order]], linewidths=0, alpha=0.85)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(heading, fontsize=11, color=theme["ink"], loc="left", pad=8)

    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=7, color=color, label=name) for color, name in zip(colors, names)]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.03, 0.875), ncol=3, frameon=False, fontsize=9.5, labelcolor=theme["ink2"], handletextpad=0.2, columnspacing=1.6)

    metrics = [("Accuracy", accuracy), ("Balanced accuracy", balanced_accuracy), ("Class Balance Accuracy", class_balance_accuracy)]
    for column, (heading, table) in enumerate([("Model 1", ALL_MAJORITY), ("Model 2", PARTITIONED)], start=1):
        ax = fig.add_subplot(lower[0, column])
        style_axes(ax, theme, grid_axis="x")
        values = [function(table) for _, function in metrics]
        positions = np.arange(len(metrics))[::-1]
        bar_colors = [theme["neutral"], theme["neutral"], theme["series"][0]]
        ax.barh(positions, values, height=0.5, color=bar_colors)
        for position, value in zip(positions, values):
            ax.text(value + 0.02, position, f"{value:.1%}", va="center", ha="left", fontsize=10.5, color=theme["ink"])
        ax.set_yticks(positions)
        ax.set_yticklabels([name for name, _ in metrics], fontsize=10, color=theme["ink2"])
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax.set_title(f"{heading} scores", fontsize=11, color=theme["ink"], loc="left", pad=8)

    note = fig.add_subplot(lower[0, 0])
    note.axis("off")
    note.text(
        0.0,
        1.12,
        "Accuracy counts correct answers,\nso it cannot see that Model 1\nnever finds a minority class.\n\n"
        "Class Balance Accuracy scores\neach class by the smaller of its\nrecall and precision, then averages.",
        fontsize=10,
        color=theme["ink2"],
        va="top",
        ha="left",
        linespacing=1.4,
        transform=note.transAxes,
    )
    save(fig, "same-accuracy", mode)


# --------------------------------------------------------------------------
# Figure 2. What balanced accuracy misses and CBA catches
# --------------------------------------------------------------------------


def fixed_recall_matrix(ratio: float, recall: float = 0.9, minority: float = 1000.0) -> list[list[float]]:
    """Three classes, one `ratio` times larger. Every class has the same recall."""
    sizes = [ratio * minority, minority, minority]
    miss = (1 - recall) / 2
    return [[size * (recall if i == j else miss) for j in range(3)] for i, size in enumerate(sizes)]


def figure_precision_blind_spot(mode: str) -> None:
    theme = THEMES[mode]
    ratios = np.logspace(0, 3, 121)
    tables = [fixed_recall_matrix(ratio) for ratio in ratios]
    lines = [
        ("Accuracy and balanced accuracy", [balanced_accuracy(t) for t in tables], theme["series"][1]),
        ("Macro precision", [macro_precision(t) for t in tables], theme["series"][2]),
        ("Class Balance Accuracy", [class_balance_accuracy(t) for t in tables], theme["series"][0]),
    ]
    fig, ax = new_figure(theme, 9.2, 5.2)
    fig.subplots_adjust(left=0.08, right=0.74, top=0.74, bottom=0.13)
    titles(
        fig,
        theme,
        "Balanced accuracy ignores precision. Class Balance Accuracy does not.",
        "A three-class model keeps 90% recall on every class while the majority class grows. False alarms swamp the small classes.",
    )
    style_axes(ax, theme)
    for name, values, color in lines:
        ax.plot(ratios, values, color=color, linewidth=2, solid_capstyle="round")
        ax.scatter([ratios[-1]], [values[-1]], s=42, color=color, edgecolors=theme["surface"], linewidths=2, zorder=3)
    # Accuracy equals balanced accuracy here because every class has the same recall.
    if any(abs(accuracy(t) - balanced_accuracy(t)) > 1e-9 for t in tables):
        raise ValueError("accuracy and balanced accuracy should coincide in this scenario")
    end_labels = {
        "Accuracy and balanced accuracy": lines[0][1][-1],
        "Macro precision": lines[1][1][-1] + 0.035,
        "Class Balance Accuracy": lines[2][1][-1] - 0.035,
    }
    for name, values, _ in lines:
        text = f"{name}  {values[-1]:.0%}".replace("Accuracy and balanced accuracy", "Accuracy and\nbalanced accuracy")
        ax.text(ratios[-1] * 1.22, end_labels[name], text, fontsize=10, color=theme["ink"], va="center", ha="left", linespacing=1.3)
    handles = [plt.Line2D([], [], color=color, linewidth=2, label=name) for name, _, color in lines]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.03, 0.865), ncol=3, frameon=False, fontsize=9.5, labelcolor=theme["ink2"], handlelength=1.4, columnspacing=1.6)
    ax.set_xscale("log")
    ax.set_xlim(1, 1000)
    ax.set_ylim(0, 1)
    ax.set_xticks([1, 10, 100, 1000])
    ax.set_xticklabels(["1 : 1", "10 : 1", "100 : 1", "1,000 : 1"])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Majority class size relative to each minority class", fontsize=10, color=theme["ink2"], labelpad=8)
    ax.minorticks_off()
    save(fig, "precision-blind-spot", mode)


# --------------------------------------------------------------------------
# Figure 3. The lower bound (Theorem 3.2.1) on simulated confusion matrices
# --------------------------------------------------------------------------


def figure_lower_bound(mode: str) -> None:
    theme = THEMES[mode]
    rng = np.random.default_rng(321)
    xs: list[float] = []
    ys: list[float] = []
    while len(xs) < 3000:
        k = int(rng.integers(3, 7))
        sizes = rng.integers(20, 2000, k)
        quality = rng.uniform(0.05, 0.97)
        table = np.zeros((k, k))
        for i, size in enumerate(sizes):
            weights = rng.dirichlet(np.ones(k) * 0.6) * (1 - quality)
            weights[i] += quality
            table[i] = rng.multinomial(size, weights / weights.sum())
        if (table.sum(axis=0) == 0).any():
            continue
        rows = table.tolist()
        xs.append(min(balanced_accuracy(rows), macro_precision(rows)))
        ys.append(class_balance_accuracy(rows))
    fig, ax = new_figure(theme, 6.6, 6.2)
    fig.subplots_adjust(left=0.13, right=0.95, top=0.80, bottom=0.12)
    titles(
        fig,
        theme,
        "A guaranteed floor",
        "3,000 simulated confusion matrices with 3 to 6 classes.\nClass Balance Accuracy never exceeds macro recall or macro precision.",
    )
    style_axes(ax, theme, grid_axis="both")
    ax.plot([0, 1], [0, 1], color=theme["axis"], linewidth=1.5)
    ax.scatter(xs, ys, s=9, color=theme["series"][0], alpha=0.45, linewidths=0)
    ax.text(0.60, 0.665, "CBA = the smaller macro score", rotation=41.5, fontsize=9.5, color=theme["ink2"], ha="center", va="center")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ticks = [0, 0.25, 0.5, 0.75, 1]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Smaller of macro recall and macro precision", fontsize=10, color=theme["ink2"], labelpad=8)
    ax.set_ylabel("Class Balance Accuracy", fontsize=10, color=theme["ink2"], labelpad=8)
    ax.set_aspect("equal")
    save(fig, "lower-bound", mode)


# --------------------------------------------------------------------------
# Citation figures
# --------------------------------------------------------------------------


def load_citations() -> list[dict]:
    with CITATIONS.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def figure_citations_by_year(rows: list[dict], mode: str) -> None:
    theme = THEMES[mode]
    colors = group_colors(theme)
    dated = [row for row in rows if row["year"]]
    if not dated:
        return
    cited_years = [int(row["year"]) for row in dated]
    years = list(range(min(cited_years), max(cited_years) + 1))
    counts = {group: [0] * len(years) for group in GROUP_ORDER}
    for row in dated:
        if int(row["year"]) in years:
            counts[usage_group(row["usage"])][years.index(int(row["year"]))] += 1
    fig, ax = new_figure(theme, 10, 5.4)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.74, bottom=0.10)
    undated = len(rows) - len(dated)
    titles(
        fig,
        theme,
        f"{len(rows)} works cite the dissertation, and most arrived after 2018",
        "Citing works by publication year and by what they cite it for."
        + (f" Not shown: {undated} undated." if undated else ""),
    )
    style_axes(ax, theme)
    bottom = np.zeros(len(years))
    for group in GROUP_ORDER:
        values = np.array(counts[group])
        ax.bar(years, values, bottom=bottom, width=0.62, color=colors[group], edgecolor=theme["surface"], linewidth=1.2, label=group)
        bottom += values
    for year, total in zip(years, bottom):
        ax.text(year, total + 0.5, f"{int(total)}", ha="center", va="bottom", fontsize=10, color=theme["ink"])
    marker_x = SKLEARN_RELEASE_YEAR + 0.5
    ax.axvline(marker_x, color=theme["muted"], linewidth=1)
    ax.text(
        marker_x - 0.12,
        bottom.max() * 0.98,
        "Sept 2018: scikit-learn 0.20 ships\nbalanced_accuracy_score, and its\nuser guide cites the dissertation",
        fontsize=9.5,
        color=theme["ink2"],
        ha="right",
        va="top",
        linespacing=1.35,
    )
    ax.set_xticks(years)
    ax.set_ylim(0, bottom.max() * 1.12)
    ax.legend(loc="upper left", bbox_to_anchor=(-0.01, 1.2), ncol=4, frameon=False, fontsize=9.5, labelcolor=theme["ink2"], handlelength=1, handleheight=1, columnspacing=1.4)
    save(fig, "citations-by-year", mode)


def horizontal_bars(rows_counted: list[tuple[str, int]], theme: dict, title: str, subtitle: str, name: str, mode: str, *, colors: list[str] | None = None, width: float = 9.2, left: float = 0.36) -> None:
    labels = [label for label, _ in rows_counted]
    values = [value for _, value in rows_counted]
    height = 1.75 + 0.36 * len(labels)
    fig, ax = new_figure(theme, width, height)
    top = 1 - 1.15 / height
    fig.subplots_adjust(left=left, right=0.93, top=top, bottom=0.04)
    titles(fig, theme, title, subtitle, top=1 - 0.2 / height)
    style_axes(ax, theme, grid_axis="x")
    positions = np.arange(len(labels))[::-1]
    ax.barh(positions, values, height=0.56, color=colors or theme["series"][0])
    for position, value in zip(positions, values):
        ax.text(value + max(values) * 0.012, position, f"{value:,}", va="center", ha="left", fontsize=10, color=theme["ink"])
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=10, color=theme["ink2"])
    ax.set_xlim(0, max(values) * 1.08)
    ax.tick_params(axis="x", labelbottom=False)
    save(fig, name, mode)


def figure_disciplines(rows: list[dict], mode: str) -> None:
    theme = THEMES[mode]
    counted = Counter(row["discipline"] for row in rows).most_common()
    fields = len([name for name, _ in counted if name != "Not determined"])
    horizontal_bars(
        counted,
        theme,
        f"A statistics thesis read in {fields} fields",
        "Citing works by discipline of the citing work.",
        "disciplines",
        mode,
    )


def figure_usage(rows: list[dict], mode: str) -> None:
    theme = THEMES[mode]
    colors = group_colors(theme)
    counted = Counter(row["usage"] for row in rows).most_common()
    horizontal_bars(
        counted,
        theme,
        "What citing works take from the dissertation",
        "One label per citing work, assigned from the citing passage.",
        "usage",
        mode,
        colors=[colors[usage_group(label)] for label, _ in counted],
    )


def figure_reach(rows: list[dict], mode: str) -> None:
    theme = THEMES[mode]
    confirmed = (row for row in rows if row["cited_by"] and row["usage"] != "Not determined")
    ranked = sorted(confirmed, key=lambda row: -int(row["cited_by"]))[:12]
    counted = [(f"{row['short_ref']}", int(row["cited_by"])) for row in ranked]
    horizontal_bars(
        counted,
        theme,
        "Second-order reach",
        "The most-cited works that cite the dissertation, by their own citation count.",
        "reach",
        mode,
        left=0.40,
    )


# --------------------------------------------------------------------------
# Idea lineage timeline
# --------------------------------------------------------------------------

LINEAGE = [
    (
        "A metric built for skewed classes",
        "Class Balance Accuracy (Ch. 3)",
        [(2017, "CBA-phi"), (2019, "Class Balance\nMetrics"), (2020, "IAM, worst-\ngroup accuracy"), (2023, "Long-tail\nknowledge in LLMs"), (2024, "Metrics\nReloaded")],
    ),
    (
        "Report several metrics, not one",
        "Measure comparisons (Ch. 2, 3)",
        [(2019, "Model Cards,\nGLUE"), (2020, "MCC over F1\nand accuracy"), (2021, "Benchmark\nLottery"), (2022, "HELM,\nBIG-bench")],
    ),
    (
        "Optimize the balanced objective",
        "Instance selection by CBA (Ch. 4)",
        [(2017, "Focal loss"), (2019, "Class-balanced\nloss, LDAM"), (2021, "Logit\nadjustment"), (2022, "Data\npruning"), (2025, "DRoP")],
    ),
    (
        "One expert per class",
        "Class Expert Ensembling (Ch. 5)",
        [(2020, "LFME"), (2021, "RIDE, ACE"), (2022, "SADE"), (2023, "BalPoE,\nFrugalGPT"), (2024, "Mixtral"), (2025, "RouteLLM")],
    ),
    (
        "Ship the code",
        "climbR package (Ch. 6)",
        [(2017, "imbalanced-\nlearn"), (2018, "PyCM,\nscikit-learn 0.20"), (2019, "Multi-\nImbalance"), (2021, "Reproducibility\nchecklists"), (2022, "Hugging Face\nEvaluate"), (2024, "lm-eval\nharness")],
    ),
]


def figure_lineage(mode: str) -> None:
    theme = THEMES[mode]
    fig, ax = new_figure(theme, 11.5, 6.6)
    fig.subplots_adjust(left=0.02, right=0.985, top=0.82, bottom=0.07)
    titles(
        fig,
        theme,
        "Five ideas from 2013 and where the field took them",
        "Each row starts at a chapter of the dissertation. Later points are related work in the same line of thought, not direct descendants.",
    )
    ax.set_facecolor(theme["surface"])
    for side in ax.spines.values():
        side.set_visible(False)
    first, last = 2013, 2025
    label_width = 4.4
    ax.set_xlim(first - label_width, last + 0.6)
    ax.set_ylim(-0.62, len(LINEAGE) - 0.3)
    ax.set_yticks([])
    ax.set_xticks(range(first, last + 1, 2))
    ax.tick_params(colors=theme["muted"], length=0, labelsize=10)
    for year in range(first, last + 1, 2):
        ax.axvline(year, color=theme["grid"], linewidth=1, zorder=0)
    for row, (idea, chapter, points) in enumerate(LINEAGE):
        y = len(LINEAGE) - 1 - row
        color = theme["series"][0]
        ax.plot([first, max(year for year, _ in points)], [y, y], color=theme["axis"], linewidth=2, zorder=1, solid_capstyle="round")
        ax.scatter([first], [y], s=130, color=color, edgecolors=theme["surface"], linewidths=2, zorder=3)
        ax.text(first - 0.35, y + 0.12, idea, fontsize=11, fontweight="bold", color=theme["ink"], ha="right", va="center")
        ax.text(first - 0.35, y - 0.16, chapter, fontsize=9.5, color=theme["ink2"], ha="right", va="center")
        above = False
        previous_year = None
        for year, name in points:
            above = (not above) if previous_year is not None and year - previous_year <= 1 else False
            previous_year = year
            ax.scatter([year], [y], s=64, color=theme["series"][1], edgecolors=theme["surface"], linewidths=2, zorder=3)
            offset, anchor = (0.15, "bottom") if above else (-0.17, "top")
            ax.text(year, y + offset, name, fontsize=8.8, color=theme["ink2"], ha="center", va=anchor, linespacing=1.15)
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", markersize=10, color=theme["series"][0], label="Dissertation (2013)"),
        plt.Line2D([], [], marker="o", linestyle="", markersize=7, color=theme["series"][1], label="Later work on the same idea"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.025, 0.875), ncol=2, frameon=False, fontsize=9.5, labelcolor=theme["ink2"], handletextpad=0.3)
    save(fig, "idea-lineage", mode)


def main() -> None:
    plt.rcParams["font.family"] = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
    for mode in THEMES:
        figure_same_accuracy(mode)
        figure_precision_blind_spot(mode)
        figure_lower_bound(mode)
        figure_lineage(mode)
        if CITATIONS.exists():
            rows = load_citations()
            figure_citations_by_year(rows, mode)
            figure_disciplines(rows, mode)
            figure_usage(rows, mode)
            figure_reach(rows, mode)
        else:
            print("data/citations.csv not found, skipping citation figures")


if __name__ == "__main__":
    main()
