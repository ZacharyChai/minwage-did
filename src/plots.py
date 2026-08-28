"""Figures: parallel trends, event study, placebo distribution, robustness forest."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.dpi": 130,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
})

TREAT_C = "#c1121f"
CTRL_C = "#1d3557"
POLICY = pd.Timestamp("2024-01-01")


def plot_parallel_trends(df: pd.DataFrame, outcome: str, label: str, path: Path) -> None:
    """Group-mean of `outcome`, each state first demeaned to its own 2023 average
    so the plot shows *co-movement*, not level gaps. Normalized to Dec 2023 = 0."""
    d = df[["state", "date", "treat", outcome]].dropna().copy()
    base = (
        d[(d.date >= "2023-01-01") & (d.date <= "2023-12-01")]
        .groupby("state")[outcome].mean().rename("base")
    )
    d = d.join(base, on="state")
    d["norm"] = d[outcome] - d["base"]
    g = d.groupby(["treat", "date"])["norm"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(9, 5))
    for tv, c, lab in [(1, TREAT_C, "Treated (Jan 2024 raisers)"),
                       (0, CTRL_C, "Control (never-treated)")]:
        s = g[g.treat == tv]
        ax.plot(s["date"], s["norm"], color=c, lw=2, label=lab)
    ax.axvline(POLICY, color="k", ls="--", lw=1)
    ax.axhline(0, color="grey", lw=0.8)
    ax.annotate("min. wage\nincrease", (POLICY, ax.get_ylim()[1]),
                textcoords="offset points", xytext=(6, -28), fontsize=8)
    ax.set_title(f"Parallel trends check — {label}\n(each state demeaned to its 2023 average)")
    ax.set_ylabel("deviation from 2023 mean")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_event_study(es: pd.DataFrame, label: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    pre = es[es.event_time < 0]
    post = es[es.event_time >= 0]
    for seg, c in [(pre, "#6c757d"), (post, TREAT_C)]:
        ax.errorbar(seg["event_time"], seg["coef"],
                    yerr=[seg["coef"] - seg["lo"], seg["hi"] - seg["coef"]],
                    fmt="o", ms=4, color=c, ecolor=c, elinewidth=1, capsize=2)
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(-0.5, color="k", ls="--", lw=1)
    ax.set_title(f"Event study — {label}")
    ax.set_xlabel("months since minimum-wage increase (Jan 2024 = 0; ref = −1)")
    ax.set_ylabel("coefficient (log points)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_placebo_distribution(dist: pd.DataFrame, real_coef: float, label: str, path: Path) -> None:
    d = dist.dropna(subset=["coef"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(d["coef"], bins=12, color="#adb5bd", edgecolor="white")
    ax.axvline(real_coef, color=TREAT_C, lw=2,
               label=f"real 2024 estimate = {real_coef:+.3f}")
    ax.axvline(0, color="k", lw=0.8)
    pctl = (d["coef"] < real_coef).mean() * 100
    ax.set_title(f"Placebo (in-time) distribution — {label}\n"
                 f"real estimate at the {pctl:.0f}th percentile of placebo estimates")
    ax.set_xlabel("DiD coefficient from a fake policy date")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_robustness_forest(grid: pd.DataFrame, label: str, path: Path) -> None:
    g = grid[grid["window"].str.startswith("2022-07") & ~grid["drop_covid"]].copy()
    g["spec"] = g["control"] + " / " + g["treated"] + " / " + g["fe"]
    g = g.sort_values(["treated", "fe", "control"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.5, 0.4 * len(g) + 1.5))
    y = np.arange(len(g))
    ax.errorbar(g["coef"], y, xerr=[g["coef"] - g["ci_lo"], g["ci_hi"] - g["coef"]],
                fmt="o", ms=5, color=CTRL_C, ecolor="#6c757d", capsize=2)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(g["spec"])
    ax.invert_yaxis()
    ax.set_xlabel("DiD coefficient (log points)")
    ax.set_title(f"Robustness to control group & sample — {label}")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
