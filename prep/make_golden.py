"""Write golden.jsonl from keys/P*.json: two lines per case, the decision and the rows.

Code written by Claude Code on Nov 8, 2026; the choices in it are the author's (cases/INDEX.md,
"Choices"): two lines per case, slices by decision and hub, normal accounts get a rows line whose
right answer is empty. The two grader names, "decision" and "rows", are defined in aml_graders.py.

    python prep/make_golden.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
HUBS = {"P05", "P07", "P09", "P11", "P14", "P16"}  # laundering accounts in many attempts
FIELDS = ("id", "slice", "input", "expected", "source")  # the order of the fields in a golden line


def group(key: dict) -> str:
    """The slice a case belongs to: "close", "escalate-hub" or "escalate-single"."""
    if not key["laundering"]:
        return "close"
    return "escalate-hub" if key["case"] in HUBS else "escalate-single"


def source(key: dict) -> str:
    """Where the expected answer comes from, for a reader of golden.jsonl."""
    path = f"keys/{key['case']}.json"
    if not key["laundering"]:
        return f"{path}, normal account"
    if len(key["attempts"]) > 1:
        return f"{path}, hub: {len(key['attempts'])} attempts"
    attempt = key["attempts"][0]
    return f"{path}, attempt #{attempt['n']} {attempt['type']}"


def golden_lines(key: dict) -> list[dict]:
    """The two golden lines of one case: its decision, and its laundering rows."""
    case, slice_name = key["case"], group(key)
    # rows labelled laundering outside any attempt count as laundering rows too (none in P01-P32)
    rows = key["laundering_rows"] + key["labelled_rows_outside_attempts"]
    decision = "ESCALATE" if key["laundering"] else "CLOSE"
    shared = {"input": f"cases/{case}.md", "source": source(key)}
    return [
        {
            "id": f"{case}-decision",
            "slice": f"decision-{slice_name}",
            "expected": {"grader": "decision", "value": decision},
            **shared,
        },
        {
            "id": f"{case}-rows",
            "slice": f"rows-{slice_name}",
            "expected": {"grader": "rows", "laundering": rows},
            **shared,
        },
    ]


def main() -> None:
    """Writes golden.jsonl from every key in keys/."""
    keys = [json.loads(path.read_text()) for path in sorted((ROOT / "keys").glob("P*.json"))]
    lines = [line for key in keys for line in golden_lines(key)]
    with (ROOT / "golden.jsonl").open("w") as f:
        for line in lines:
            f.write(json.dumps({field: line[field] for field in FIELDS}) + "\n")
    print(f"golden.jsonl written: {len(lines)} lines")


if __name__ == "__main__":
    main()
