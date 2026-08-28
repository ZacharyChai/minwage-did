"""
The econometrics: parallel-trends check, headline DiD, event study, placebo,
and the robustness grid. Every estimate is TWFE (state + calendar-month fixed
effects) with standard errors clustered on state.

Run `python src/analysis.py` to regenerate everything in output/ and figures/.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

from build_panel import build, estimation_frame
from config import PLACEBO_DATES, POLICY_DATE
from plots import (
    plot_event_study,
    plot_parallel_trends,
    plot_placebo_distribution,
    plot_robustness_forest,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

warnings.filterwarnings("ignore", category=FutureWarning)

# Baseline estimation window. The parallel-trends figure (see figures/) shows
# treated and control states only converge onto a common path from ~mid-2022,
# after the uneven COVID rebound washes out. So the headline window starts
# 2022-07 (18 clean pre-period months); a 2021-01 start is kept as a
# longer-window robustness row.
BASE_START = "2022-07-01"
LONG_START = "2021-01-01"
BASE_END = "2026-07-01"
PT_START = "2018-01-01"   # full history, for the visual parallel-trends check only
ES_LEAD_CAP = -17         # 18 pre-period months available from BASE_START

OUTCOME_LABELS = {
    "lemp_retail": "log retail employment",
    "lemp_leisure_hosp": "log leisure & hospitality employment",
    "lemp_total_nonfarm": "log total nonfarm employment (placebo outcome)",
    "lshare_retail": "log retail share of nonfarm",
    "lshare_leisure_hosp": "log leisure & hosp. share of nonfarm",
}


# ---------------------------------------------------------------------------
# 1. Headline DiD
# ---------------------------------------------------------------------------
def did(df: pd.DataFrame, outcome: str, fe: str = "state + month") -> pf.Feols:
    return pf.feols(f"{outcome} ~ did | {fe}", data=df, vcov={"CRV1": "state"})


# ---------------------------------------------------------------------------
# 2. Event study
# ---------------------------------------------------------------------------
def _fit_event_study(df: pd.DataFrame, outcome: str, lead_cap: int, lag_cap: int, ref: int):
    d = df.assign(et=df["event_time"].clip(lower=lead_cap, upper=lag_cap).astype(int))
    return pf.feols(
        f"{outcome} ~ i(et, treat, ref={ref}) | state + month",
        data=d, vcov={"CRV1": "state"},
    )


def event_study(
    df: pd.DataFrame,
    outcome: str,
    lead_cap: int = -17,
    lag_cap: int = 30,
    ref: int = -1,
) -> pd.DataFrame:
    m = _fit_event_study(df, outcome, lead_cap, lag_cap, ref)
    tidy = m.tidy().reset_index()
    tidy = tidy[tidy["Coefficient"].str.contains("et::")].copy()
    tidy["event_time"] = tidy["Coefficient"].str.extract(r"et::(-?\d+):").astype(int)
    tidy = tidy.rename(columns={"Estimate": "coef", "2.5%": "lo", "97.5%": "hi"})
    ref_row = pd.DataFrame([{"event_time": ref, "coef": 0.0, "lo": 0.0, "hi": 0.0,
                             "Std. Error": 0.0, "Pr(>|t|)": np.nan}])
    return (
        pd.concat([tidy[["event_time", "coef", "lo", "hi", "Std. Error", "Pr(>|t|)"]], ref_row])
        .sort_values("event_time")
        .reset_index(drop=True)
    )


def pretrend_summary(es: pd.DataFrame) -> dict:
    """Descriptive read of the pre-period coefficients."""
    pre = es[es["event_time"] < -1]
    t = pre["coef"] / pre["Std. Error"].replace(0, np.nan)
    return {
        "n_pre_coefs": len(pre),
        "n_pre_sig_5pct": int((pre["Pr(>|t|)"] < 0.05).sum()),
        "max_abs_t_pre": float(t.abs().max()),
        "max_abs_pre_effect_logpts": float(pre["coef"].abs().max()),
    }


def pretrend_joint_test(df: pd.DataFrame, outcome: str, lead_cap=-17, lag_cap=30, ref=-1) -> dict:
    """Proper joint Wald test that every pre-period event-time coefficient is 0."""
    m = _fit_event_study(df, outcome, lead_cap, lag_cap, ref)
    names = list(m.coef().index)
    pre_idx = [
        i for i, c in enumerate(names)
        if c.startswith("et::") and int(c.split("::")[1].split(":")[0]) < ref
    ]
    if not pre_idx:
        return {"joint_pretrend_F": np.nan, "joint_pretrend_p": np.nan, "n_terms": 0}
    R = np.zeros((len(pre_idx), len(names)))
    for r, j in enumerate(pre_idx):
        R[r, j] = 1.0
    w = m.wald_test(R=R, distribution="chi2")
    return {
        "joint_pretrend_stat": float(w.iloc[0]),
        "joint_pretrend_p": float(w.iloc[-1]),
        "n_terms": len(pre_idx),
    }


# ---------------------------------------------------------------------------
# 3. Placebo test
# ---------------------------------------------------------------------------
def placebo_run(panel: pd.DataFrame, fake_date: str, outcome: str) -> dict:
    """Re-anchor the panel to a fake policy date and estimate DiD using ONLY
    data strictly before the real 2024 policy, so a genuine effect cannot leak."""
    p = build(anchor=fake_date)
    df = estimation_frame(p, control="strict", start=None, end="2023-12-01")
    fk = pd.Timestamp(fake_date)
    df = df[df["date"] >= fk - pd.DateOffset(years=3)]
    m = did(df, outcome)
    row = m.tidy().loc["did"]
    return {
        "fake_date": fake_date,
        "outcome": outcome,
        "coef": float(row["Estimate"]),
        "se": float(row["Std. Error"]),
        "p": float(row["Pr(>|t|)"]),
        "n_obs": len(df),
    }


def in_time_placebo_distribution(panel: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Slide the fake policy date across every month of the pre-period and
    collect the DiD estimate. The real estimate should sit in the tail of this
    placebo distribution if the design is picking up the policy."""
    rows = []
    for m in pd.date_range("2018-06-01", "2023-06-01", freq="3MS"):
        try:
            r = placebo_run(panel, m.strftime("%Y-%m-%d"), outcome)
            rows.append(r)
        except Exception as e:  # noqa: BLE001
            rows.append({"fake_date": m, "outcome": outcome, "coef": np.nan,
                         "se": np.nan, "p": np.nan, "n_obs": 0, "err": str(e)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Robustness grid
# ---------------------------------------------------------------------------
def robustness_grid(panel: pd.DataFrame, outcome: str) -> pd.DataFrame:
    specs = []
    windows = [("2022-07 start (baseline)", BASE_START), ("2021-01 start (long)", LONG_START)]
    for control in ["strict", "broad", "border"]:
        for treated in ["all", "legislated", "indexed"]:
            for win_tag, win_start in windows:
                for drop_covid in [False, True]:
                    if drop_covid and win_start == BASE_START:
                        continue  # no COVID months in the baseline window anyway
                    for fe, fe_tag in [("state + month", "twoway"),
                                       ("state + month + divmonth", "division x month")]:
                        df = estimation_frame(
                            panel, control=control, treated=treated,
                            start=win_start, end=BASE_END, drop_covid=drop_covid,
                        )
                        if df["treat"].sum() == 0 or df["treat"].eq(0).sum() == 0:
                            continue
                        m = did(df, outcome, fe=fe)
                        r = m.tidy().loc["did"]
                        specs.append({
                            "outcome": outcome, "control": control, "treated": treated,
                            "window": win_tag, "drop_covid": drop_covid, "fe": fe_tag,
                            "coef": float(r["Estimate"]), "se": float(r["Std. Error"]),
                            "ci_lo": float(r["2.5%"]), "ci_hi": float(r["97.5%"]),
                            "p": float(r["Pr(>|t|)"]),
                            "n_treated_states": int(df.loc[df.treat.eq(1), "state"].nunique()),
                            "n_control_states": int(df.loc[df.treat.eq(0), "state"].nunique()),
                            "n_obs": len(df),
                        })
    return pd.DataFrame(specs)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main() -> None:
    panel = build()
    panel.to_parquet(ROOT / "data" / "processed" / "panel.parquet", index=False)

    primary_outcomes = ["lemp_retail", "lemp_leisure_hosp", "lemp_total_nonfarm"]
    summary_rows = []
    es_store = {}

    # --- parallel trends (visual) + headline + event study, per outcome ---
    for oc in primary_outcomes:
        df_pt = estimation_frame(panel, control="strict", start=PT_START, end=BASE_END)
        plot_parallel_trends(df_pt, oc, OUTCOME_LABELS[oc], FIG / f"parallel_trends_{oc}.png")

        df = estimation_frame(panel, control="strict", start=BASE_START, end=BASE_END)
        es = event_study(df, oc)
        es.to_csv(OUT / f"event_study_{oc}.csv", index=False)
        es_store[oc] = es
        plot_event_study(es, OUTCOME_LABELS[oc], FIG / f"event_study_{oc}.png")

        pt = pretrend_summary(es)
        ptj = pretrend_joint_test(df, oc)

        for fe, fe_tag in [("state + month", "twoway"),
                           ("state + month + divmonth", "division x month")]:
            hr = did(df, oc, fe=fe).tidy().loc["did"]
            summary_rows.append({
                "outcome": oc, "fe": fe_tag,
                "did_coef": float(hr["Estimate"]),
                "did_se": float(hr["Std. Error"]),
                "did_ci_lo": float(hr["2.5%"]),
                "did_ci_hi": float(hr["97.5%"]),
                "did_p": float(hr["Pr(>|t|)"]),
                "pct_effect": float(np.expm1(hr["Estimate"]) * 100),
                **pt, **ptj,
            })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "headline_summary.csv", index=False)

    # --- placebo ---
    placebo_rows = []
    for fd in PLACEBO_DATES:
        for oc in ["lemp_retail", "lemp_leisure_hosp"]:
            placebo_rows.append(placebo_run(panel, fd, oc))
    placebo = pd.DataFrame(placebo_rows)
    placebo.to_csv(OUT / "placebo_fixed_dates.csv", index=False)

    ri_rows = []
    for oc in ["lemp_retail", "lemp_leisure_hosp"]:
        dist = in_time_placebo_distribution(panel, oc)
        dist.to_csv(OUT / f"placebo_distribution_{oc}.csv", index=False)
        real = summary.loc[(summary.outcome == oc) & (summary.fe == "twoway"), "did_coef"].iloc[0]
        pc = dist["coef"].dropna()
        ri_rows.append({
            "outcome": oc,
            "real_coef": real,
            "n_placebo": len(pc),
            "ri_p_two_sided": float((pc.abs() >= abs(real)).mean()),
            "placebo_mean": float(pc.mean()),
            "placebo_sd": float(pc.std()),
            "real_percentile": float((pc < real).mean() * 100),
        })
        plot_placebo_distribution(dist, real, OUTCOME_LABELS[oc],
                                  FIG / f"placebo_distribution_{oc}.png")
    ri = pd.DataFrame(ri_rows)
    ri.to_csv(OUT / "randomization_inference.csv", index=False)

    # --- robustness grid ---
    grids = []
    for oc in ["lemp_retail", "lemp_leisure_hosp"]:
        g = robustness_grid(panel, oc)
        grids.append(g)
        plot_robustness_forest(g, OUTCOME_LABELS[oc], FIG / f"robustness_{oc}.png")
    robustness = pd.concat(grids, ignore_index=True)
    robustness.to_csv(OUT / "robustness_grid.csv", index=False)

    # --- console report ---
    pd.set_option("display.width", 160, "display.max_columns", 20)
    print(f"\n=== HEADLINE (control = strict never-treated, {BASE_START}..{BASE_END}) ===")
    print(summary.round(4).to_string(index=False))
    print("\n=== PLACEBO (fixed fake dates, pre-2024 data only) ===")
    print(placebo.round(4).to_string(index=False))
    print("\n=== RANDOMIZATION INFERENCE (real vs sliding in-time placebos) ===")
    print(ri.round(4).to_string(index=False))
    print("\n=== ROBUSTNESS GRID (retail) ===")
    print(robustness[robustness.outcome == "lemp_retail"].round(4).to_string(index=False))
    print("\n=== ROBUSTNESS GRID (leisure & hospitality) ===")
    print(robustness[robustness.outcome == "lemp_leisure_hosp"].round(4).to_string(index=False))
    print(f"\nfigures -> {FIG}\noutput   -> {OUT}")


if __name__ == "__main__":
    main()
