"""
Pull state-level employment series from FRED and cache them locally.

Uses FRED's public CSV download endpoint (fredgraph.csv), which needs no API
key for a fixed list of series. If you have a FRED API key and prefer the JSON
API, set the FRED_API_KEY environment variable and pass use_api=True.

Every series is cached as data/raw/<series_id>.csv so re-runs are offline and
the exact vintage is reproducible. Delete the cache to force a refresh.
"""

from __future__ import annotations

import io
import os
import time
from pathlib import Path

import pandas as pd
import requests

from config import OUTCOMES, SAMPLE_END, SAMPLE_START, STATE_FIPS, series_ids

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

CSV_ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv"
API_ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"


def _fetch_csv(series_id: str) -> pd.Series:
    r = requests.get(CSV_ENDPOINT, params={"id": series_id}, timeout=30)
    r.raise_for_status()
    if not r.text.lstrip().startswith("observation_date"):
        raise ValueError(f"{series_id}: unexpected response (not a FRED CSV)")
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.set_index("date")["value"].rename(series_id)


def _fetch_api(series_id: str) -> pd.Series:
    key = os.environ["FRED_API_KEY"]
    r = requests.get(
        API_ENDPOINT,
        params={
            "series_id": series_id,
            "api_key": key,
            "file_type": "json",
            "observation_start": SAMPLE_START,
            "observation_end": SAMPLE_END,
        },
        timeout=30,
    )
    r.raise_for_status()
    obs = r.json()["observations"]
    s = pd.Series(
        {pd.Timestamp(o["date"]): pd.to_numeric(o["value"], errors="coerce") for o in obs},
        name=series_id,
    )
    s.index.name = "date"
    return s


def get_series(series_id: str, use_api: bool = False, force: bool = False) -> pd.Series:
    cache = RAW_DIR / f"{series_id}.csv"
    if cache.exists() and not force:
        s = pd.read_csv(cache, parse_dates=["date"]).set_index("date")["value"]
        return s.rename(series_id)
    s = _fetch_api(series_id) if use_api else _fetch_csv(series_id)
    s.rename("value").rename_axis("date").to_frame().to_csv(cache)
    time.sleep(0.3)  # be polite to FRED
    return s.rename(series_id)


def build_long_panel(states: list[str] | None = None, **kw) -> pd.DataFrame:
    """Return a tidy long panel: one row per (state, date, outcome)."""
    states = states or sorted(STATE_FIPS)
    frames = []
    for st in states:
        ids = series_ids(st)
        for outcome in OUTCOMES:
            sid = ids[outcome]
            s = get_series(sid, **kw)
            s = s[(s.index >= SAMPLE_START) & (s.index <= SAMPLE_END)]
            frames.append(
                pd.DataFrame(
                    {
                        "state": st,
                        "date": s.index,
                        "outcome": outcome,
                        "employment": s.values,   # thousands of persons
                        "series_id": sid,
                    }
                )
            )
    panel = pd.concat(frames, ignore_index=True)
    return panel.sort_values(["outcome", "state", "date"]).reset_index(drop=True)


if __name__ == "__main__":
    import sys

    force = "--force" in sys.argv
    use_api = "--api" in sys.argv
    panel = build_long_panel(force=force, use_api=use_api)
    out = Path(__file__).resolve().parents[1] / "data" / "processed" / "employment_long.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out, index=False)
    n_states = panel["state"].nunique()
    print(f"pulled {panel['series_id'].nunique()} series / {n_states} states")
    print(f"date range: {panel['date'].min():%Y-%m} .. {panel['date'].max():%Y-%m}")
    print(f"missing employment values: {panel['employment'].isna().sum()}")
    print(f"wrote {out}")
