"""
Central configuration: policy classification, FRED series construction, sample window.

Everything the analysis needs to know about *the world* (which states did what, when)
lives here so the modeling code stays about econometrics, not bookkeeping.

Sources for the minimum-wage classification (retrieved 2026-08):
  - Economic Policy Institute, "Twenty-two states will increase their minimum wages
    on January 1 [2024]" (epi.org)
  - Ballotpedia, "Minimum wage increases in 2024"
  - Epstein Becker Green, "State and Local Minimum Wage Increases on January 1, 2024"
  - U.S. Dept. of Labor, Wage and Hour Division, "State Minimum Wage Laws"
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Sample window
# ---------------------------------------------------------------------------
# Start in 2015 to give a long pre-period for the parallel-trends check while
# staying in the post-Great-Recession recovery regime. The event study and the
# headline DiD use a trimmed window (see analysis.py); the raw pull grabs
# everything so we can re-slice without re-downloading.
SAMPLE_START = "2015-01-01"
SAMPLE_END = "2026-07-01"          # last month currently on FRED for these series

# Policy date: the Jan 1, 2024 round of state minimum-wage increases.
POLICY_DATE = "2024-01-01"

# Placebo ("fake") policy dates. Each is analyzed using ONLY data that predates
# the real policy, so a real 2024 effect cannot leak in.
PLACEBO_DATES = ["2022-01-01", "2019-01-01"]

# COVID window to optionally drop in robustness runs.
COVID_START = "2020-03-01"
COVID_END = "2021-06-01"

# ---------------------------------------------------------------------------
# State FIPS codes (for building BLS/FRED SM series IDs)
# ---------------------------------------------------------------------------
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16",
    "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22",
    "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40",
    "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
    "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56",
}

# ---------------------------------------------------------------------------
# FRED series construction
# ---------------------------------------------------------------------------
# Outcome series. "retail" and "leisure_hosp" are the treated industries
# (low-wage, minimum-wage-exposed). "total_nonfarm" is the normalizer /
# placebo-outcome (should NOT respond to a minimum-wage change if anything does).
def series_ids(state: str) -> dict[str, str]:
    fips = STATE_FIPS[state]
    return {
        # All employees, retail trade, thousands, SA, monthly
        "retail": f"SMS{fips}000004200000001",
        # All employees, leisure & hospitality, thousands, SA, monthly (friendly ID)
        "leisure_hosp": f"{state}LEIH",
        # All employees, total nonfarm, thousands, SA, monthly (friendly ID)
        "total_nonfarm": f"{state}NA",
    }


OUTCOMES = ["retail", "leisure_hosp", "total_nonfarm"]

# ---------------------------------------------------------------------------
# Treatment group: states that raised the statewide minimum wage on 2024-01-01
# ---------------------------------------------------------------------------
# rate_2023 / rate_2024 in $/hour. "kind":
#   "legislated"  -> scheduled step increase from a statute or ballot measure
#   "indexed"     -> automatic annual cost-of-living adjustment (small)
# For states with tiered rates (NJ small employers, NY upstate/downstate, MN
# large/small) we use the *standard large-employer* rate, which is the headline
# and the one that binds for most retail/hospitality payroll.
TREATED = {
    "AK": dict(rate_2023=10.85, rate_2024=11.73, kind="indexed"),
    "AZ": dict(rate_2023=13.85, rate_2024=14.35, kind="indexed"),
    "CA": dict(rate_2023=15.50, rate_2024=16.00, kind="indexed"),
    "CO": dict(rate_2023=13.65, rate_2024=14.42, kind="indexed"),
    "CT": dict(rate_2023=15.00, rate_2024=15.69, kind="indexed"),
    "DE": dict(rate_2023=11.75, rate_2024=13.25, kind="legislated"),
    "HI": dict(rate_2023=12.00, rate_2024=14.00, kind="legislated"),
    "IL": dict(rate_2023=13.00, rate_2024=14.00, kind="legislated"),
    "ME": dict(rate_2023=13.80, rate_2024=14.15, kind="indexed"),
    "MD": dict(rate_2023=13.25, rate_2024=15.00, kind="legislated"),
    "MI": dict(rate_2023=10.10, rate_2024=10.33, kind="indexed"),
    "MN": dict(rate_2023=10.59, rate_2024=10.85, kind="indexed"),
    "MO": dict(rate_2023=12.00, rate_2024=12.30, kind="indexed"),
    "MT": dict(rate_2023=9.95, rate_2024=10.30, kind="indexed"),
    "NE": dict(rate_2023=10.50, rate_2024=12.00, kind="legislated"),   # 2022 ballot
    "NJ": dict(rate_2023=14.13, rate_2024=15.13, kind="legislated"),
    "NY": dict(rate_2023=14.20, rate_2024=15.00, kind="legislated"),   # upstate std
    "OH": dict(rate_2023=10.10, rate_2024=10.45, kind="indexed"),
    "RI": dict(rate_2023=13.00, rate_2024=14.00, kind="legislated"),
    "SD": dict(rate_2023=10.80, rate_2024=11.20, kind="indexed"),
    "VT": dict(rate_2023=13.18, rate_2024=13.67, kind="indexed"),
    "WA": dict(rate_2023=15.74, rate_2024=16.28, kind="indexed"),
}

for _s, _d in TREATED.items():
    _d["delta"] = round(_d["rate_2024"] - _d["rate_2023"], 2)
    _d["pct_change"] = round(_d["delta"] / _d["rate_2023"] * 100, 1)

TREATED_STATES = sorted(TREATED)
LEGISLATED_STATES = sorted(s for s, d in TREATED.items() if d["kind"] == "legislated")
INDEXED_STATES = sorted(s for s, d in TREATED.items() if d["kind"] == "indexed")

# ---------------------------------------------------------------------------
# States raising mid-2024 (NOT on Jan 1). Excluded from BOTH groups: they are
# neither cleanly treated at the event date nor clean controls.
# ---------------------------------------------------------------------------
MIDYEAR_2024 = {
    "FL": "2024-09-30",   # ballot ramp, $12 -> $13
    "NV": "2024-07-01",   # $10.25/$11.25 -> $12.00 flat
    "OR": "2024-07-01",   # indexed
}

# ---------------------------------------------------------------------------
# Control groups
# ---------------------------------------------------------------------------
# CONTROL_STRICT: "never-treated" bloc. States on the federal $7.25 floor with
# no state legislation, plus WV ($8.75, unchanged since 2016). No minimum-wage
# change anywhere near the event window in either direction.
CONTROL_STRICT = [
    "AL", "GA", "ID", "IN", "IA", "KS", "KY", "LA", "MS", "NH",
    "NC", "ND", "OK", "PA", "SC", "TN", "TX", "UT", "WI", "WY", "WV",
]

# CONTROL_BROAD: strict bloc plus states with a statewide minimum above $7.25
# that did NOT change it on 2024-01-01 (NM and VA last stepped up in Jan 2023).
# Larger n, but "recently treated" -> a softer parallel-trends assumption.
CONTROL_BROAD = sorted(CONTROL_STRICT + ["NM", "VA"])

# ---------------------------------------------------------------------------
# State adjacency (contiguous land borders) for the border-pairs robustness
# control. Only the entries we need (treated states + their neighbors) matter,
# but the full map is here for completeness.
# ---------------------------------------------------------------------------
NEIGHBORS = {
    "AL": ["FL", "GA", "MS", "TN"],
    "AK": [],
    "AZ": ["CA", "CO", "NV", "NM", "UT"],
    "AR": ["LA", "MO", "MS", "OK", "TN", "TX"],
    "CA": ["AZ", "NV", "OR"],
    "CO": ["AZ", "KS", "NE", "NM", "OK", "UT", "WY"],
    "CT": ["MA", "NY", "RI"],
    "DE": ["MD", "NJ", "PA"],
    "FL": ["AL", "GA"],
    "GA": ["AL", "FL", "NC", "SC", "TN"],
    "HI": [],
    "ID": ["MT", "NV", "OR", "UT", "WA", "WY"],
    "IL": ["IN", "IA", "KY", "MO", "WI"],
    "IN": ["IL", "KY", "MI", "OH"],
    "IA": ["IL", "MN", "MO", "NE", "SD", "WI"],
    "KS": ["CO", "MO", "NE", "OK"],
    "KY": ["IL", "IN", "MO", "OH", "TN", "VA", "WV"],
    "LA": ["AR", "MS", "TX"],
    "ME": ["NH"],
    "MD": ["DE", "PA", "VA", "WV"],
    "MA": ["CT", "NH", "NY", "RI", "VT"],
    "MI": ["IN", "OH", "WI"],
    "MN": ["IA", "ND", "SD", "WI"],
    "MS": ["AL", "AR", "LA", "TN"],
    "MO": ["AR", "IL", "IA", "KS", "KY", "NE", "OK", "TN"],
    "MT": ["ID", "ND", "SD", "WY"],
    "NE": ["CO", "IA", "KS", "MO", "SD", "WY"],
    "NV": ["AZ", "CA", "ID", "OR", "UT"],
    "NH": ["ME", "MA", "VT"],
    "NJ": ["DE", "NY", "PA"],
    "NM": ["AZ", "CO", "OK", "TX", "UT"],
    "NY": ["CT", "MA", "NJ", "PA", "VT"],
    "NC": ["GA", "SC", "TN", "VA"],
    "ND": ["MN", "MT", "SD"],
    "OH": ["IN", "KY", "MI", "PA", "WV"],
    "OK": ["AR", "CO", "KS", "MO", "NM", "TX"],
    "OR": ["CA", "ID", "NV", "WA"],
    "PA": ["DE", "MD", "NJ", "NY", "OH", "WV"],
    "RI": ["CT", "MA"],
    "SC": ["GA", "NC"],
    "SD": ["IA", "MN", "MT", "NE", "ND", "WY"],
    "TN": ["AL", "AR", "GA", "KY", "MO", "MS", "NC", "VA"],
    "TX": ["AR", "LA", "NM", "OK"],
    "UT": ["AZ", "CO", "ID", "NV", "NM", "WY"],
    "VT": ["MA", "NH", "NY"],
    "VA": ["KY", "MD", "NC", "TN", "WV"],
    "WA": ["ID", "OR"],
    "WV": ["KY", "MD", "OH", "PA", "VA"],
    "WI": ["IL", "IA", "MI", "MN"],
    "WY": ["CO", "ID", "MT", "NE", "SD", "UT"],
}


# Census divisions — used for division x calendar-month fixed effects, which
# absorb region-wide shocks (e.g. differential post-COVID recovery, internal
# migration) that a plain calendar-month effect cannot.
CENSUS_DIVISION = {
    "CT": "New England", "ME": "New England", "MA": "New England",
    "NH": "New England", "RI": "New England", "VT": "New England",
    "NJ": "Middle Atlantic", "NY": "Middle Atlantic", "PA": "Middle Atlantic",
    "IL": "East North Central", "IN": "East North Central", "MI": "East North Central",
    "OH": "East North Central", "WI": "East North Central",
    "IA": "West North Central", "KS": "West North Central", "MN": "West North Central",
    "MO": "West North Central", "NE": "West North Central", "ND": "West North Central",
    "SD": "West North Central",
    "DE": "South Atlantic", "FL": "South Atlantic", "GA": "South Atlantic",
    "MD": "South Atlantic", "NC": "South Atlantic", "SC": "South Atlantic",
    "VA": "South Atlantic", "WV": "South Atlantic",
    "AL": "East South Central", "KY": "East South Central", "MS": "East South Central",
    "TN": "East South Central",
    "AR": "West South Central", "LA": "West South Central", "OK": "West South Central",
    "TX": "West South Central",
    "AZ": "Mountain", "CO": "Mountain", "ID": "Mountain", "MT": "Mountain",
    "NV": "Mountain", "NM": "Mountain", "UT": "Mountain", "WY": "Mountain",
    "AK": "Pacific", "CA": "Pacific", "HI": "Pacific", "OR": "Pacific", "WA": "Pacific",
}


def border_control_states() -> list[str]:
    """Non-treated, non-midyear states that share a land border with >=1 treated
    state. These are the most 'economically comparable' controls a skeptic would
    ask for: same regional labor market, just across a policy line."""
    treated = set(TREATED_STATES)
    exclude = treated | set(MIDYEAR_2024)
    out = set()
    for t in TREATED_STATES:
        for nb in NEIGHBORS[t]:
            if nb not in exclude:
                out.add(nb)
    return sorted(out)


# ---------------------------------------------------------------------------
# Convenience: the full estimation frame for a given control definition
# ---------------------------------------------------------------------------
def analysis_states(control: str = "strict") -> dict[str, list[str]]:
    controls = {
        "strict": CONTROL_STRICT,
        "broad": CONTROL_BROAD,
        "border": border_control_states(),
    }[control]
    return {"treated": TREATED_STATES, "control": controls}
