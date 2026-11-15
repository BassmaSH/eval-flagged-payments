"""Keep a run's answers on disk as they arrive, so a run that stops can pick up where it was.

    results/<run>.partial.json   written after every golden line, removed when the run is complete

A case is kept on resume only when every golden line of it was graded: a case with one line done, or
with a failed call, is asked again, so both of its lines always grade the same answer.

Code written by Claude Code on Nov 15, 2026, for the author, who asked what happens to a run that
stops halfway.
"""

import json
from pathlib import Path

GRADED = {"pass_first", "pass_retry", "fail"}
RECORDS = ("usage", "thinking", "thinking_tokens")  # what a model system notes per case file


def complete_cases(results: list[dict], cases: list[dict]) -> set[str]:
    """Returns the case files whose golden lines were all graded in these results."""
    status = {result["id"]: result["status"] for result in results}
    lines_of: dict[str, list[str]] = {}
    for case in cases:
        lines_of.setdefault(case["input"], []).append(case["id"])
    return {
        case_file
        for case_file, line_ids in lines_of.items()
        if all(status.get(line_id) in GRADED for line_id in line_ids)
    }


def save(path: Path, results: list[dict], system: object) -> None:
    """Writes the results so far, with what the system noted for each case (tokens, reasoning)."""
    records = {name: getattr(system, name, {}) for name in RECORDS}
    path.write_text(json.dumps({"results": results, **records}, indent=1, ensure_ascii=False))


def resume(path: Path, cases: list[dict], system: object) -> dict[str, dict]:
    """Returns the results to keep from a stopped run, and gives the system back its notes for them.

    Args:
        path: the partial file; when it does not exist, nothing is kept.
        cases: the golden lines of the run.
        system: the system about to be run; its usage, thinking and thinking_tokens are refilled.

    Returns:
        golden line id -> the saved result, for the complete cases only.
    """
    if not path.exists():
        return {}
    saved = json.loads(path.read_text())
    kept = complete_cases(saved["results"], cases)
    for name in RECORDS:
        notes = getattr(system, name, None)
        if notes is not None:
            notes.update({case: v for case, v in saved.get(name, {}).items() if case in kept})
    input_of = {case["id"]: case["input"] for case in cases}
    return {r["id"]: r for r in saved["results"] if input_of.get(r["id"]) in kept}
