"""One line per case, to screen candidates without reading every table.

Boilerplate, written by Claude on Nov 7, 2026 (like make_case.py): it only counts what is in cases/<id>.md.

    python peek.py P17 P18 P19
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent

for case in sys.argv[1:]:
    rows = [line.split("|")[1:-1] for line in (HERE / "cases" / f"{case}.md").read_text().splitlines()
            if line.startswith("| T")]
    out = [r for r in rows if r[2].strip() == "out"]
    into = [r for r in rows if r[2].strip() == "in"]
    print(f"{case}: {len(rows)} rows | {len(out)} out, to {len({r[3] for r in out})} accounts | "
          f"{len(into)} in, from {len({r[3] for r in into})} accounts | "
          f"{len({r[5] for r in rows})} currencies | {len({r[6] for r in rows})} formats | "
          f"largest {max(float(r[4]) for r in rows):,.2f}")
