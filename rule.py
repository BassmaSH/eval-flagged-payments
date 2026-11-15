"""The baseline with no model: a counting rule a monitoring team could write.

    system("cases/P03.md")  ->  '{"reason": "paid 8+ accounts within 3 days", "decision": "ESCALATE", "rows": [...]}'

Escalate if the account paid MIN_ACCOUNTS or more different accounts within WINDOW; cite the payments out in that
window. This detects one of the data's eight laundering patterns, fan-out. Same contract as system.py, so the
same graders score it.

Code written by Claude Code on Nov 8, 2026, with the brief's example rule; the thresholds were fixed before the
runs and are the author's to change.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

from case_table import TIME_FORMAT, read_transactions

HERE = Path(__file__).parent
MIN_ACCOUNTS = 8
WINDOW = timedelta(days=3)


def system(case_file: str) -> str:
    """Returns the rule's answer to one case, in the same JSON as a model's."""
    paid = [(t.id, datetime.strptime(t.time, TIME_FORMAT), t.counterparty)
            for t in read_transactions(HERE / case_file) if t.direction == "out"]
    for _, start, _ in paid:
        window = [(row_id, account) for row_id, time, account in paid if start <= time < start + WINDOW]
        if len({account for _, account in window}) >= MIN_ACCOUNTS:
            return json.dumps({"reason": f"paid {MIN_ACCOUNTS}+ accounts within {WINDOW.days} days",
                               "decision": "ESCALATE", "rows": [row_id for row_id, _ in window]})
    return json.dumps({"reason": "no burst of payments out", "decision": "CLOSE", "rows": []})
