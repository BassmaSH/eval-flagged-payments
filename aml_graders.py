"""The two graders of this eval, "decision" and "rows", on top of evals-kit's five.

Code written by Claude Code on Nov 8, 2026, from the author's choices (cases/INDEX.md, "Choices"); the author
reviews it line by line. Named aml_graders.py, not graders.py, because evals-kit's runner imports its own `graders`.

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
    """'T3', 't003' and 'T003' are the same row (the author's choice, Nov 8); anything else is kept as written."""
    m = re.fullmatch(r"[Tt]0*(\d+)", str(r).strip())
    return f"T{int(m.group(1)):03d}" if m else str(r).strip()


def grade_decision(answer, expected):
    """Passes when the decision is the expected word. Only case and spaces are forgiven: "ESCALATE." fails."""
    decision = " ".join(str(answer.get("decision", "")).split()).upper()
    if decision == expected["value"]:
        return True, "ok"
    return False, f"expected {expected['value']}, got {answer.get('decision')!r}"


def grade_rows(answer, expected):
    """The author's rule, written before any run.
    Laundering account: more than half of the laundering rows cited, and no other row.
    Normal account: no row cited."""
    rows = answer.get("rows")
    if not isinstance(rows, list):
        return False, f"rows is not a list: {rows!r}"
    cited = {row_id(r) for r in rows}
    laundering = set(expected["laundering"])
    right = cited & laundering
    wrong = sorted(cited - laundering)

    if not laundering:
        return (True, "ok") if not cited else (False, f"normal account, cited {wrong}")
    if wrong:
        return False, f"cited normal rows {wrong} ({len(right)}/{len(laundering)} laundering rows cited)"
    if 2 * len(right) <= len(laundering):
        return False, f"cited {len(right)}/{len(laundering)} laundering rows, needs more than half"
    return True, f"ok: {len(right)}/{len(laundering)} laundering rows, no normal row"


GRADERS = {"decision": grade_decision, "rows": grade_rows}


def grade(output, expected):
    """One answer against one golden line -> (passed, reason)."""
    name = expected["grader"]
    if name not in GRADERS:
        return kit_grade(output, expected)  # evals-kit's five; raises ValueError on an unknown name
    answer, why_not = parse(output)
    if answer is None:
        return False, why_not
    return GRADERS[name](answer, expected)
