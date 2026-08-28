"""
End-to-end pipeline. Reproduces every number, table, and figure from scratch.

    python run_all.py            # use the committed data cache
    python run_all.py --refresh  # re-pull everything from FRED first

Steps:
  1. fetch_fred.py   -> data/raw/*.csv, data/processed/employment_long.parquet
  2. build_panel.py  -> data/processed/panel.parquet
  3. analysis.py     -> output/*.csv, figures/*.png
"""

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
PY = sys.executable


def run(script: str, *args: str) -> None:
    print(f"\n{'=' * 70}\n  {script} {' '.join(args)}\n{'=' * 70}", flush=True)
    subprocess.run([PY, str(SRC / script), *args], check=True, cwd=SRC)


if __name__ == "__main__":
    refresh = "--refresh" in sys.argv
    run("fetch_fred.py", *(["--force"] if refresh else []))
    run("build_panel.py")
    run("analysis.py")
    print("\nDone. See MEMO.md for the written interpretation.")
