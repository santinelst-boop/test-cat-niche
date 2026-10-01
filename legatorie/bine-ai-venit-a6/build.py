"""Montaj „Bine ai venit!” A6 4-up pe SRA4, doar față.

Refolosește montajul din ../rugaciune-a6/build.py (același model ca Momentum).
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "rugaciune-a6"))
import build as montaj  # noqa: E402

montaj.NAME = "Bine ai venit"
montaj.PAGES = [HERE / "sursa" / "fata.jpg"]

if __name__ == "__main__":
    montaj.build(HERE / "BineAiVenit_A6_4up_SRA4_fata.pdf")
    print("ok")
