"""One line per case, to screen candidates without reading every table.

    python peek.py P17 P18 P19

Written by Claude on Nov 7, 2026: it only counts what is in cases/<id>.md.
"""

import sys
from pathlib import Path

from case_table import read_transactions

HERE = Path(__file__).parent


def summary(case_id: str) -> str:
    """Returns the counts that show at a glance whether an account looks like an alert."""
    rows = read_transactions(HERE / "cases" / f"{case_id}.md")
    out = [t for t in rows if t.direction == "out"]
    into = [t for t in rows if t.direction == "in"]
    return (
        f"{case_id}: {len(rows)} rows | "
        f"{len(out)} out, to {len({t.counterparty for t in out})} accounts | "
        f"{len(into)} in, from {len({t.counterparty for t in into})} accounts | "
        f"{len({t.currency for t in rows})} currencies | {len({t.format for t in rows})} formats | "
        f"largest {max(float(t.amount) for t in rows):,.2f}"
    )


def main(argv: list[str]) -> None:
    """Prints one summary line per case id given."""
    if not argv:
        sys.exit(__doc__)
    for case_id in argv:
        print(summary(case_id))


if __name__ == "__main__":
    main(sys.argv[1:])
