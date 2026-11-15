"""Tests for saving a run as it goes and resuming it (checkpoint.py, run.run_and_save). No API call.

    python tests/test_checkpoint.py
    pytest tests/test_checkpoint.py

Plain asserts, like the other tests. Code written by Claude Code on Nov 15, 2026.
"""

import contextlib
import json
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import run  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import checkpoint  # noqa: E402

CASES = [
    {"id": f"{case}-{part}", "slice": part, "input": f"cases/{case}.md", "expected": {}}
    for case in ("A", "B", "C")
    for part in ("decision", "rows")
]


class CountingSystem:
    """Stands in for a model: answers with the case file's name and notes one "usage" per call."""

    def __init__(self, stop_after: int | None = None, fail_on: str = "") -> None:
        self.usage: dict[str, list[int]] = {}
        self.calls: list[str] = []
        self.stop_after = stop_after
        self.fail_on = fail_on

    def __call__(self, case_file: str) -> str:
        """Answers one case, or stops, or fails, as set up."""
        if self.stop_after is not None and len(self.calls) >= self.stop_after:
            raise KeyboardInterrupt  # the terminal was closed
        if case_file == self.fail_on:
            raise RuntimeError("no credit left")
        self.calls.append(case_file)
        self.usage[case_file] = [100, 10]
        return case_file


def in_temporary_results(test: "callable") -> "callable":
    """Points run.py's results folder at an empty temporary one for the length of a test."""

    def wrapped() -> None:
        saved = run.RESULTS
        with tempfile.TemporaryDirectory() as folder:
            run.RESULTS = Path(folder)
            try:
                test()
            finally:
                run.RESULTS = saved

    wrapped.__name__ = test.__name__
    return wrapped


def passing_grade(output: str, expected: dict) -> tuple[bool, str]:
    return True, "ok"


def result(line_id: str, status: str) -> dict:
    return {"id": line_id, "slice": "s", "status": status, "attempts": []}


def test_a_case_is_complete_only_when_all_its_lines_were_graded():
    done = [
        result("A-decision", "fail"),
        result("A-rows", "pass_first"),
        result("B-decision", "fail"),
    ]
    assert checkpoint.complete_cases(done, CASES) == {"cases/A.md"}, "B has one line of two"
    failed = [result("A-decision", "infra_error"), result("A-rows", "infra_error")]
    assert checkpoint.complete_cases(failed, CASES) == set(), "a failed call is asked again"


@in_temporary_results
def test_every_line_is_on_disk_when_the_run_stops():
    run.grade = passing_grade
    system = CountingSystem(stop_after=2)  # answers A twice (two lines), B once, then stops
    with contextlib.suppress(KeyboardInterrupt):
        run.run_and_save(CASES, system, "stopped")
    saved = json.loads((run.RESULTS / "stopped.partial.json").read_text())
    assert [r["id"] for r in saved["results"]] == ["A-decision", "A-rows"]
    assert not (run.RESULTS / "stopped.json").exists(), "an unfinished run has no final file"


@in_temporary_results
def test_a_resumed_run_equals_an_uninterrupted_one_and_asks_nothing_twice():
    run.grade = passing_grade
    whole = run.run_and_save(CASES, CountingSystem(), "whole")

    first = CountingSystem(stop_after=3)  # stops inside case B: one line done, one not
    with contextlib.suppress(KeyboardInterrupt):
        run.run_and_save(CASES, first, "resumed")
    second = CountingSystem()
    resumed = run.run_and_save(CASES, second, "resumed")

    assert resumed == whole
    assert "cases/A.md" not in second.calls, "A was complete: not asked again"
    assert second.calls.count("cases/B.md") == 2, "B was half done: both its lines asked again"
    assert set(second.usage) == {"cases/A.md", "cases/B.md", "cases/C.md"}, "A's tokens were kept"
    assert not (run.RESULTS / "resumed.partial.json").exists(), "the partial file is removed"
    assert json.loads((run.RESULTS / "resumed.json").read_text()) == whole


@in_temporary_results
def test_a_run_with_failed_calls_is_not_saved_as_finished_and_resumes():
    run.grade = passing_grade
    with_hole = run.run_and_save(CASES, CountingSystem(fail_on="cases/B.md"), "hole")
    assert [r["status"] for r in with_hole][2:4] == ["infra_error", "infra_error"]
    assert not (run.RESULTS / "hole.json").exists(), "its name stays free for the real run"
    assert (run.RESULTS / "hole.partial.json").exists()

    credit_is_back = CountingSystem()
    complete = run.run_and_save(CASES, credit_is_back, "hole")
    assert credit_is_back.calls == ["cases/B.md", "cases/B.md"], "only the missing case is asked"
    assert all(r["status"] == "pass_first" for r in complete)
    assert (run.RESULTS / "hole.json").exists()
    assert not (run.RESULTS / "hole.partial.json").exists()


def test_a_system_without_notes_can_be_saved_and_resumed():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "rule.partial.json"
        checkpoint.save(path, [result("A-decision", "fail"), result("A-rows", "fail")], system=len)
        assert set(checkpoint.resume(path, CASES, system=len)) == {"A-decision", "A-rows"}


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    print(f"testing checkpoint.py: {len(tests)} checks")
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
