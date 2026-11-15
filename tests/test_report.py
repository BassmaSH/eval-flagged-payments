"""Tests for report.py's generated page. No API call.

    python tests/test_report.py
    pytest tests/test_report.py

Plain asserts, like the other tests. Code written by Claude Code on Nov 15, 2026.
"""

import contextlib
import io
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import report  # noqa: E402


def generated_answers() -> str:
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        report.print_answers()
    return printed.getvalue()


def test_the_answers_page_is_what_the_command_generates():
    """docs/ANSWERS.md is never edited by hand: it must equal the command's output."""
    on_disk = (ROOT / "docs" / "ANSWERS.md").read_text()
    assert on_disk == generated_answers(), "run: python report.py answers > docs/ANSWERS.md"


def test_the_answers_page_has_every_account_and_every_run():
    page = generated_answers()
    assert page.count("\n## P") == 32
    for label, _ in report.ANSWER_RUNS:
        assert page.count(f"- **{label}:**") == 32, label
    assert page.count("- **Claude, three reruns:**") == 32


def test_a_cue_counts_only_after_the_task_has_been_restated():
    restated = "the prompt asks to flag the suspicious rows. " + "x " * 200
    deciding = "x " * 200 + "but the alert is triggered, so i must find something."
    assert not report.cited_while_deciding(restated, report.CUES["the alert"])
    assert report.cited_while_deciding(deciding, report.CUES["the alert"])
    instruction = report.CUES["the instruction to flag suspicious rows"]
    assert not report.cited_while_deciding(restated, instruction), "at the start: not counted"
    assert report.cited_while_deciding(
        "x " * 200 + "however, the prompt asks me to flag suspicious rows", instruction
    )


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    print(f"testing report.py: {len(tests)} checks")
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
