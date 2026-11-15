"""Rebuild the README's tables from the saved answers. No API call, no key, standard library only.

    python report.py

Every answer in results/ is graded again with aml_graders.py against golden.jsonl, so the tables below follow
from the answers and the scoring code as they are in the repo today, not from a verdict stored at run time.
Token counts and costs are not here: the runs of Nov 8-11 did not save them (see results/<name>.meta.json for
runs made since Nov 15).

Code written by Claude Code on Nov 15, 2026, for the author.
"""
import functools
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "evals_kit"))
from aml_graders import grade, parse, row_id  # noqa: E402

GOLDEN = {g["id"]: g for g in map(json.loads, (HERE / "golden.jsonl").read_text().splitlines())}
SLICES = [("decision: escalate, single scheme", "decision-escalate-single"),
          ("decision: escalate, hub account", "decision-escalate-hub"),
          ("decision: close", "decision-close"),
          ("evidence: escalate, single scheme", "rows-escalate-single"),
          ("evidence: escalate, hub account", "rows-escalate-hub"),
          ("evidence: close", "rows-close")]


def answers(run_name: str) -> dict[str, str]:
    """golden line id -> the answer that was graded (the last attempt)."""
    saved = json.loads((HERE / "results" / f"{run_name}.json").read_text())
    return {line["id"]: line["attempts"][-1].get("output", "") for line in saved}


@functools.cache
def scores(run_name: str) -> dict[str, tuple[int, int]]:
    """slice -> (lines passed, lines in the slice), graded again now. Each run is graded once."""
    passed, total = {}, {}
    for line_id, output in answers(run_name).items():
        golden = GOLDEN[line_id]
        total[golden["slice"]] = total.get(golden["slice"], 0) + 1
        passed[golden["slice"]] = passed.get(golden["slice"], 0) + grade(output, golden["expected"])[0]
    return {s: (passed[s], total[s]) for s in total}


def percent(run_name: str, slice_name: str) -> str:
    passed, total = scores(run_name)[slice_name]
    return f"{round(100 * passed / total)}%"


def rows_cited(run_name: str) -> tuple[int, int]:
    """(laundering rows cited, other rows cited) over the 32 accounts."""
    laundering = other = 0
    for line_id, output in answers(run_name).items():
        expected = GOLDEN[line_id]["expected"]
        if expected["grader"] != "rows":
            continue
        answer, _ = parse(output)
        rows = answer.get("rows") if answer else None
        cited = {row_id(r) for r in rows} if isinstance(rows, list) else set()
        laundering += len(cited & set(expected["laundering"]))
        other += len(cited - set(expected["laundering"]))
    return laundering, other


TERMS = ["fan-out", "fan-in", "pass-through", "layering", "structuring", "recurring"]


def vocabulary(run_name: str) -> list[int]:
    """For each term, the number of accounts (of 32) whose "reason" contains it."""
    counts = dict.fromkeys(TERMS, 0)
    for line_id, output in answers(run_name).items():
        if not line_id.endswith("-decision"):  # the -rows line holds the same answer
            continue
        answer, _ = parse(output)
        reason = str((answer or {}).get("reason", "")).lower()
        for spaced in ("fan out", "fan in", "pass through"):
            reason = reason.replace(spaced, spaced.replace(" ", "-"))
        for term in TERMS:
            counts[term] += term in reason
    return [counts[term] for term in TERMS]


def table(header: list[str], rows: list[list]) -> None:
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(str(cell) for cell in row) + " |")
    print()


def main() -> None:
    print("## What was measured\n")
    runs = ["rule", "mistral-small-2603", "mistral-large-2512", "mistral-large-4", "claude-opus-5-5"]
    table(["slice", "n"] + runs,
          [[label, scores("rule")[s][1]] + [percent(r, s) for r in runs] for label, s in SLICES])

    print("## Checking the harness (Large 4)\n")
    table(["run", "close", "escalate (single / hub)", "evidence (single / hub)"],
          [[label, percent(r, "decision-close"),
            f"{percent(r, 'decision-escalate-single')} / {percent(r, 'decision-escalate-hub')}",
            f"{percent(r, 'rows-escalate-single')} / {percent(r, 'rows-escalate-hub')}"]
           for label, r in [("JSON mode, temperature 0", "mistral-large-4"),
                            ("Claude's schema, temperature 0", "mistral-large-4+schema"),
                            ("Claude's schema, temperature 1", "mistral-large-4+schema-temp1")]])

    print("## Three prompt changes (Small and Large 3)\n")
    rows = []
    for variant in ("", "simulated", "objective", "both"):
        row = [variant or "nothing"]
        for model in ("mistral-small-2603", "mistral-large-2512"):
            r = f"{model}+{variant}" if variant else model
            row += [percent(r, "decision-close"),
                    f"{percent(r, 'decision-escalate-single')} / {percent(r, 'decision-escalate-hub')}",
                    " / ".join(percent(r, s) for s in ("rows-escalate-single", "rows-escalate-hub", "rows-close"))]
        rows.append(row)
    columns = ["close", "escalate (single / hub)", "evidence (single / hub / close)"]
    table(["added"] + [f"Small: {c}" for c in columns] + [f"Large 3: {c}" for c in columns], rows)

    print("## Giving Large 4 Claude's method\n")
    runs = [("Large 4", "mistral-large-4"), ("A: + method", "mistral-large-4+method"),
            ("C: + method, neutral alert", "mistral-large-4+method-neutral"), ("Claude", "claude-opus-5-5")]
    by_run = {r: scores(r) for _, r in runs}
    table([""] + [label for label, _ in runs],
          [["normal accounts closed (of 16)"] + [by_run[r]["decision-close"][0] for _, r in runs],
           ["laundering accounts caught (of 16)"]
           + [by_run[r]["decision-escalate-single"][0] + by_run[r]["decision-escalate-hub"][0] for _, r in runs],
           ["rows cited: laundering / other"] + ["{:,} / {:,}".format(*rows_cited(r)) for _, r in runs],
           ["evidence (single / hub)"]
           + [f"{percent(r, 'rows-escalate-single')} / {percent(r, 'rows-escalate-hub')}" for _, r in runs]])

    print("## The words each run uses (accounts of 32 whose reason contains the term)\n")
    names = sorted(p.name[:-5] for p in (HERE / "results").glob("*.json")
                   if p.name.count(".") == 1 and p.name != "rule.json")
    table(["run"] + TERMS, [[name] + vocabulary(name) for name in names])


if __name__ == "__main__":
    main()
