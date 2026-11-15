"""Read the transaction table of a case file (cases/<id>.md), the one format every script shares.

    read_transactions(Path("cases/P01.md"))[2]
    ->  Transaction(id="T003", time="2022/09/01 00:03", direction="out", counterparty="020 / 80BC62F10",
                    amount="58702.10", currency="Yuan", format="ACH")

Code written by Claude Code on Nov 15, 2026: the same lines were in rule.py, peek.py and the tests.
"""
from pathlib import Path
from typing import NamedTuple

TIME_FORMAT = "%Y/%m/%d %H:%M"


class Transaction(NamedTuple):
    """One row of the table, as text. direction is "out", "in" or "self", seen from the case's account."""
    id: str
    time: str
    direction: str
    counterparty: str
    amount: str
    currency: str
    format: str


def read_transactions(case_file: Path) -> list[Transaction]:
    """The rows of the table, in file order. Every other line of the file is ignored."""
    return [Transaction(*(cell.strip() for cell in line.split("|")[1:-1]))
            for line in case_file.read_text().splitlines() if line.startswith("| T")]
