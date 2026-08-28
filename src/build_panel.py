"""
Turn the raw long employment panel into the estimation frame used by every
regression and plot.

Output: data/processed/panel.parquet, one row per (state, date), wide over
outcomes, with:
  - emp_<outcome>              level, thousands
  - lemp_<outcome>             log level
  - share_<outcome>            outcome employment / total nonfarm (retail, leih)
  - group                      'treated' / 'control_strict' / 'control_broad' /
                               'control_border' / 'treated_legislated' /
                               'treated_indexed' / 'excluded'
  - treat                      1 if ever-treated (Jan 2024 raiser), else 0
  - post                       1 if date >= POLICY_DATE
  - event_time                 months since POLICY_DATE (0 = Jan 2024)
  - rel_quarter                event time bucketed to quarters
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    CENSUS_DIVISION,
    CONTROL_BROAD,
    CONTROL_STRICT,
    INDEXED_STATES,
    LEGISLATED_STATES,
    MIDYEAR_2024,
    POLICY_DATE,
    TREATED_STATES,
    border_control_states,
)

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"


def _event_time_months(dates: pd.Series, anchor: str) -> pd.Series:
    a = pd.Timestamp(anchor)
    return (dates.dt.year - a.year) * 12 + (dates.dt.month - a.month)


def build(anchor: str = POLICY_DATE) -> pd.DataFrame:
    long = pd.read_parquet(PROC / "employment_long.parquet")

    wide = (
        long.pivot_table(index=["state", "date"], columns="outcome", values="employment")
        .rename(columns=lambda c: f"emp_{c}")
        .reset_index()
    )

    for oc in ["retail", "leisure_hosp", "total_nonfarm"]:
        wide[f"lemp_{oc}"] = np.log(wide[f"emp_{oc}"])
    for oc in ["retail", "leisure_hosp"]:
        wide[f"share_{oc}"] = wide[f"emp_{oc}"] / wide["emp_total_nonfarm"]
        wide[f"lshare_{oc}"] = np.log(wide[f"share_{oc}"])

    border = set(border_control_states())

    def classify(st: str) -> str:
        if st in TREATED_STATES:
            return "treated"
        if st in MIDYEAR_2024:
            return "excluded"
        tags = []
        if st in CONTROL_STRICT:
            tags.append("strict")
        if st in CONTROL_BROAD:
            tags.append("broad")
        if st in border:
            tags.append("border")
        return "control_" + "_".join(tags) if tags else "excluded"

    wide["group"] = wide["state"].map(classify)
    wide["treat"] = wide["state"].isin(TREATED_STATES).astype(int)
    wide["treat_legislated"] = wide["state"].isin(LEGISLATED_STATES).astype(int)
    wide["treat_indexed"] = wide["state"].isin(INDEXED_STATES).astype(int)

    wide["post"] = (wide["date"] >= pd.Timestamp(anchor)).astype(int)
    wide["event_time"] = _event_time_months(wide["date"], anchor)
    wide["rel_quarter"] = np.floor(wide["event_time"] / 3).astype(int)
    wide["did"] = wide["treat"] * wide["post"]

    wide["month"] = wide["date"].dt.to_period("M").astype(str)
    wide["year"] = wide["date"].dt.year
    wide["t"] = (wide["date"].dt.year - 2015) * 12 + wide["date"].dt.month
    wide["division"] = wide["state"].map(CENSUS_DIVISION)
    wide["divmonth"] = wide["division"] + " | " + wide["month"]

    return wide.sort_values(["state", "date"]).reset_index(drop=True)


def estimation_frame(
    panel: pd.DataFrame,
    control: str = "strict",
    treated: str = "all",
    start: str | None = None,
    end: str | None = None,
    drop_covid: bool = False,
) -> pd.DataFrame:
    """Slice `panel` to one treated definition + one control definition."""
    from config import COVID_END, COVID_START

    ctrl_tag = {"strict": "strict", "broad": "broad", "border": "border"}[control]
    keep_control = panel["group"].str.contains(f"control_.*{ctrl_tag}", regex=True)

    if treated == "all":
        keep_treated = panel["treat"].eq(1)
    elif treated == "legislated":
        keep_treated = panel["treat_legislated"].eq(1)
    elif treated == "indexed":
        keep_treated = panel["treat_indexed"].eq(1)
    else:
        raise ValueError(treated)

    df = panel[keep_treated | keep_control].copy()
    # redefine `treat` for this slice: 1 for the selected treatment subset,
    # 0 for the selected controls (the pooled `treat` column marks every
    # Jan-2024 raiser, which is wrong when treated == 'legislated'/'indexed').
    df["treat"] = keep_treated.loc[df.index].astype(int)

    if start:
        df = df[df["date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["date"] <= pd.Timestamp(end)]
    if drop_covid:
        covid = (df["date"] >= pd.Timestamp(COVID_START)) & (df["date"] <= pd.Timestamp(COVID_END))
        df = df[~covid]
    df["did"] = df["treat"] * df["post"]
    return df.reset_index(drop=True)


if __name__ == "__main__":
    panel = build()
    panel.to_parquet(PROC / "panel.parquet", index=False)
    print(f"panel: {panel.shape[0]} rows, {panel['state'].nunique()} states, "
          f"{panel['date'].min():%Y-%m}..{panel['date'].max():%Y-%m}")
    print(panel.groupby("group")["state"].nunique().to_string())
    print("\ntreated legislated:", LEGISLATED_STATES)
    print("treated indexed:   ", INDEXED_STATES)
    print("border controls:   ", border_control_states())
