"""Tests for aml_graders.py: the "decision" and "rows" graders behind every score in the README.

Run:
    python test_aml_graders.py
or, with pytest:
    pytest test_aml_graders.py

Plain asserts and no pytest feature, like evals-kit's test_runner.py, so both ways run the same
checks. Code written by Claude Code on Nov 15, 2026. The three P01 cases are the author's, worked by
hand first.
"""

import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "evals_kit"))  # aml_graders imports evals-kit's graders

from aml_graders import grade  # noqa: E402
from case_table import read_transactions  # noqa: E402

# P01's key: two laundering rows, the two ends of a cycle.
ESCALATE = {"grader": "decision", "value": "ESCALATE"}
CLOSE = {"grader": "decision", "value": "CLOSE"}
P01_ROWS = {"grader": "rows", "laundering": ["T003", "T009"]}
NORMAL_ROWS = {"grader": "rows", "laundering": []}  # a normal account: nothing to cite


def answer(decision: str = "ESCALATE", rows: tuple | list = (), reason: str = "x") -> str:
    """A model's answer, as the text the grader receives."""
    return json.dumps({"reason": reason, "decision": decision, "rows": list(rows)})


# ---------------------------------------------------------------- the author's three cases on P01


def test_one_of_two_rows_escalates_right_but_fails_the_evidence():
    out = answer("ESCALATE", ["T003"])
    assert grade(out, ESCALATE)[0]
    passed, reason = grade(out, P01_ROWS)
    assert not passed and "1/2" in reason, "exactly half is not more than half"


def test_both_rows_plus_a_normal_one_fails_the_evidence():
    out = answer("ESCALATE", ["T003", "T009", "T004"])
    assert grade(out, ESCALATE)[0]
    passed, reason = grade(out, P01_ROWS)
    assert not passed and "T004" in reason, "the reason names the normal row that was cited"


def test_close_with_no_rows_fails_both_on_a_laundering_account():
    out = answer("CLOSE", [])
    assert not grade(out, ESCALATE)[0]
    passed, reason = grade(out, P01_ROWS)
    assert not passed and "0/2" in reason


# ---------------------------------------------------------------- the rows rule


def test_both_rows_and_nothing_else_passes():
    assert grade(answer(rows=["T003", "T009"]), P01_ROWS)[0]


def test_more_than_half_is_enough():
    three = {"grader": "rows", "laundering": ["T001", "T002", "T003"]}
    assert grade(answer(rows=["T001", "T002"]), three)[0], "2 of 3 is more than half"
    assert not grade(answer(rows=["T001"]), three)[0], "1 of 3 is not"
    four = {"grader": "rows", "laundering": ["T001", "T002", "T003", "T004"]}
    assert not grade(answer(rows=["T001", "T002"]), four)[0], "2 of 4 is exactly half: fails"
    assert grade(answer(rows=["T001", "T002", "T003"]), four)[0]


def test_one_normal_row_fails_even_with_every_laundering_row():
    four = {"grader": "rows", "laundering": ["T001", "T002", "T003", "T004"]}
    assert not grade(answer(rows=["T001", "T002", "T003", "T004", "T050"]), four)[0]


def test_row_ids_are_read_the_same_whatever_the_zeros_and_case():
    assert grade(answer(rows=["T3", "t009"]), P01_ROWS)[0], (
        "T3, t009 and T003, T009 are the same rows"
    )
    assert grade(answer(rows=[" T003 ", "T0009"]), P01_ROWS)[0]
    assert not grade(answer(rows=["3", "9"]), P01_ROWS)[0], "a bare number is not a row id"


def test_a_row_cited_twice_counts_once():
    assert not grade(answer(rows=["T003", "T003"]), P01_ROWS)[0], "T003 twice is still 1 of 2"


def test_normal_account_passes_only_with_no_row():
    assert grade(answer("CLOSE", []), NORMAL_ROWS)[0]
    passed, reason = grade(answer("CLOSE", ["T007"]), NORMAL_ROWS)
    assert not passed and "T007" in reason
    assert grade(answer("ESCALATE", []), NORMAL_ROWS)[0], (
        "the rows line does not look at the decision"
    )


# ---------------------------------------------------------------- the decision rule


def test_decision_both_directions():
    assert grade(answer("ESCALATE"), ESCALATE)[0]
    assert not grade(answer("CLOSE"), ESCALATE)[0]
    assert grade(answer("CLOSE"), CLOSE)[0]
    assert not grade(answer("ESCALATE"), CLOSE)[0]


def test_decision_forgives_case_and_spaces_only():
    assert grade(answer(" escalate "), ESCALATE)[0]
    assert not grade(answer("ESCALATE."), ESCALATE)[0]
    assert not grade(answer("escalate it"), ESCALATE)[0]


def test_decision_line_does_not_look_at_the_rows():
    assert grade(answer("ESCALATE", ["T999"]), ESCALATE)[0]


# ---------------------------------------------------- answers that are not what was asked


def test_broken_answers_fail_with_a_reason_and_do_not_crash():
    broken = [
        "",
        "ESCALATE",
        "Here is my answer: {",
        '["ESCALATE"]',
        "null",
        '{"reason": "x"}',
        '{"decision": null, "rows": null}',
    ]
    for out in broken:
        for expected in (ESCALATE, P01_ROWS):
            passed, reason = grade(out, expected)
            assert passed is False and reason.strip(), (out, expected)


def test_rows_given_as_text_fails():
    passed, reason = grade('{"decision": "ESCALATE", "rows": "T003, T009"}', P01_ROWS)
    assert not passed and "not a list" in reason


def test_a_failure_always_says_why_and_a_pass_says_ok():
    for out, expected in [(answer("CLOSE"), ESCALATE), (answer(rows=["T003"]), P01_ROWS)]:
        passed, reason = grade(out, expected)
        assert passed is False and reason.strip()
    assert grade(answer("ESCALATE"), ESCALATE) == (True, "ok")


def test_grader_is_pure():
    expected = {"grader": "rows", "laundering": ["T003", "T009"]}
    before = json.dumps(expected)
    out = answer(rows=["T003", "T009"])
    assert grade(out, expected) == grade(out, expected), "same inputs, same verdict"
    assert json.dumps(expected) == before, "the grader must not modify the case"


# ---------------------------------------------------------------- the link with evals-kit


def test_other_grader_names_go_to_evals_kit():
    assert grade("yes", {"grader": "exact", "value": "yes"})[0]


def test_unknown_grader_raises_value_error():
    try:
        grade(answer(), {"grader": "no_such_grader"})
    except ValueError:
        return
    raise AssertionError("an unknown grader name must raise, not fail the model")


# ---------------------------------------------------------------- on the real golden file


def golden():
    return [
        json.loads(line)
        for line in (HERE / "golden.jsonl").read_text().splitlines()
        if line.strip()
    ]


def key_of(case_id: str, lines: list[dict]) -> tuple[str, list[str]]:
    """The right decision and the laundering rows of one case, from its two golden lines."""
    decision = next(g for g in lines if g["id"] == f"{case_id}-decision")["expected"]["value"]
    rows = next(g for g in lines if g["id"] == f"{case_id}-rows")["expected"]["laundering"]
    return decision, rows


def test_the_perfect_answer_passes_every_golden_line():
    lines = golden()
    assert len(lines) == 64
    for g in lines:
        decision, rows = key_of(g["id"].split("-")[0], lines)
        passed, reason = grade(answer(decision, rows), g["expected"])
        assert passed, (g["id"], reason)


def test_always_escalate_scores_100_on_escalate_and_0_on_close():
    """The README's reading of the Mistral runs: escalating everything is 100% and 0%."""
    for g in golden():
        if g["expected"]["grader"] != "decision":
            continue
        passed, _ = grade(answer("ESCALATE", []), g["expected"])
        assert passed == (g["expected"]["value"] == "ESCALATE"), g["id"]


def test_citing_every_row_passes_no_evidence_line():
    """Citing everything always includes a normal row, so it can never pass."""
    for g in golden():
        if g["expected"]["grader"] != "rows":
            continue
        n = len(read_transactions(HERE / g["input"]))
        assert n > len(g["expected"]["laundering"]), (
            f"{g['id']}: every row is laundering, the rule breaks"
        )
        assert not grade(answer(rows=[f"T{i:03d}" for i in range(1, n + 1)]), g["expected"])[0], g[
            "id"
        ]


# ---------------------------------------------------- runner for `python test_aml_graders.py`

if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    print(f"testing aml_graders.py: {len(tests)} checks")
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [ok ] {name}")
        except Exception:
            failed += 1
            print(f"  [FAIL] {name}")
            traceback.print_exc()
    print("\nALL PASS" if not failed else f"\n{failed} FAILED")
    raise SystemExit(1 if failed else 0)
