"""The baseline with no model: a ten-line rule a monitoring team could write.

Written by Claude on Nov 8, 2026, at Bassma's request, with the brief's example rule; the rule itself is hers to
change. Same contract as system.py, so the same graders score it.

Escalate if the account paid 8 or more different accounts within 3 days; cite the payments out in that window.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
MIN_ACCOUNTS, WINDOW = 8, timedelta(days=3)


def system(input):
    rows = [line.split("|")[1:-1] for line in (HERE / input).read_text().splitlines() if line.startswith("| T")]
    out = [(r[0].strip(), datetime.strptime(r[1].strip(), "%Y/%m/%d %H:%M"), r[3].strip())
           for r in rows if r[2].strip() == "out"]
    for _, start, _ in out:
        window = [(tid, acct) for tid, t, acct in out if start <= t < start + WINDOW]
        if len({acct for _, acct in window}) >= MIN_ACCOUNTS:
            return json.dumps({"reason": f"paid {MIN_ACCOUNTS}+ accounts within 3 days", "decision": "ESCALATE",
                               "rows": [tid for tid, _ in window]})
    return json.dumps({"reason": "no burst of payments out", "decision": "CLOSE", "rows": []})
