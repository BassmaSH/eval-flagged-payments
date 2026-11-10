"""The two graders of this eval, "decision" and "rows", on top of evals-kit's five.

Written by Claude on Nov 8, 2026, at Bassma's request, from her choices (cases/INDEX.md, "Choices"); she reviews
it line by line. Named aml_graders.py, not graders.py, because evals-kit's runner imports its own `graders`.

grade(output, expected) -> (passed, reason), the SPEC §2 contract: pure, always a reason, unknown name raises.
The output is the model's text, which JSON mode makes a JSON object: {"reason", "decision", "rows"}.
"""
import json
import re

from graders import grade as kit_grade  # evals-kit's five: exact, contains_all, contains_none, numeric, abstains


def parse(output):
    """The answer as a dict, or None and why not. Broken JSON is a model failure, not a grader crash."""
    try:
        answer = json.loads(output)
    except json.JSONDecodeError:
        return None, f"not valid JSON: {output[:80]!r}"
    if not isinstance(answer, dict):
        return None, f"JSON but not an object: {output[:80]!r}"
    return answer, ""


def row_id(r):
    """'T3', 't003' and 'T003' are the same row (her choice, Nov 8); anything else is kept as written."""
    m = re.fullmatch(r"[Tt]0*(\d+)", str(r).strip())
    return f"T{int(m.group(1)):03d}" if m else str(r).strip()


def grade(output, expected):
    name = expected["grader"]
    if name not in ("decision", "rows"):
        return kit_grade(output, expected)  # raises ValueError on an unknown name
    answer, why = parse(output)
    if answer is None:
        return False, why

    if name == "decision":
        # Only the SPEC's normalisation (case, spaces): "ESCALATE." or "escalate it" fail
        decision = " ".join(str(answer.get("decision", "")).split()).upper()
        if decision == expected["value"]:
            return True, "ok"
        return False, f"expected {expected['value']}, got {answer.get('decision')!r}"

    rows = answer.get("rows")
    if not isinstance(rows, list):
        return False, f"rows is not a list: {rows!r}"
    cited = {row_id(r) for r in rows}
    laundering = set(expected["laundering"])
    normal = sorted(cited - laundering)  # anything cited that is not a laundering row
    if not laundering:  # a normal account: the right answer cites nothing
        return (True, "ok") if not cited else (False, f"normal account, cited {normal}")
    hits = cited & laundering
    # Her rule, written before any run: more than half of the laundering rows, and no normal row
    if normal:
        return False, f"cited normal rows {normal} ({len(hits)}/{len(laundering)} laundering rows cited)"
    if 2 * len(hits) <= len(laundering):
        return False, f"cited {len(hits)}/{len(laundering)} laundering rows, needs more than half"
    return True, f"ok: {len(hits)}/{len(laundering)} laundering rows, no normal row"
