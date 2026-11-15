"""Write golden.jsonl from keys/P*.json: two lines per case, one for the decision and one for the rows.

Code written by Claude Code on Nov 8, 2026; the choices in it are the author's (cases/INDEX.md, "Choices"):
two lines per case, slices by decision and hub, normal accounts get a rows line whose right answer is empty.
The two grader names, "decision" and "rows", are defined in aml_graders.py.

    python make_golden.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
HUBS = {"P05", "P07", "P09", "P11", "P14", "P16"}  # laundering accounts in many attempts


def group(key):
    if not key["laundering"]:
        return "close"
    return "escalate-hub" if key["case"] in HUBS else "escalate-single"


def source(key):
    path = f"keys/{key['case']}.json"
    if not key["laundering"]:
        return f"{path}, normal account"
    if len(key["attempts"]) > 1:
        return f"{path}, hub: {len(key['attempts'])} attempts"
    a = key["attempts"][0]
    return f"{path}, attempt #{a['n']} {a['type']}"


lines = []
for path in sorted((HERE / "keys").glob("P*.json")):
    key = json.loads(path.read_text())
    case, g = key["case"], group(key)
    # rows labelled laundering outside any attempt count as laundering rows too (none in P01-P32)
    rows = key["laundering_rows"] + key["labelled_rows_outside_attempts"]
    common = {"input": f"cases/{case}.md", "source": source(key)}
    lines.append({"id": f"{case}-decision", "slice": f"decision-{g}",
                  "expected": {"grader": "decision", "value": "ESCALATE" if key["laundering"] else "CLOSE"},
                  **common})
    lines.append({"id": f"{case}-rows", "slice": f"rows-{g}",
                  "expected": {"grader": "rows", "laundering": rows}, **common})

with (HERE / "golden.jsonl").open("w") as f:
    for line in lines:
        f.write(json.dumps({k: line[k] for k in ("id", "slice", "input", "expected", "source")}) + "\n")
print(f"golden.jsonl written: {len(lines)} lines")
