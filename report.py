"""Rebuild the README's tables from the saved answers. No API call, no key, standard library only.

    python report.py

Every answer in results/ is graded again with aml_graders.py against golden.jsonl, so the tables
below follow from the answers and the scoring code as they are in the repo today, not from a verdict
stored at run time. Token counts and costs are not here: the runs of Nov 8-11 did not save them (see
results/<name>.meta.json for runs made since Nov 15).

Code written by Claude Code on Nov 15, 2026, for the author.
"""

import functools
import json
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
# evals_kit is a copy of github.com/BassmaSH/evals-kit
sys.path[:0] = [str(SRC), str(SRC / "evals_kit")]
import paths  # noqa: E402
from aml_graders import grade, parse, row_id  # noqa: E402
from stats import exact_interval, paired_p_value  # noqa: E402
from vocabulary import CASH_TERMS, PATTERNS, named  # noqa: E402

GOLDEN = {g["id"]: g for g in map(json.loads, paths.GOLDEN.read_text().splitlines())}
SLICES = [
    ("decision: escalate, single scheme", "decision-escalate-single"),
    ("decision: escalate, hub account", "decision-escalate-hub"),
    ("decision: close", "decision-close"),
    ("evidence: escalate, single scheme", "rows-escalate-single"),
    ("evidence: escalate, hub account", "rows-escalate-hub"),
    ("evidence: close", "rows-close"),
]


def answers(run_name: str) -> dict[str, str]:
    """Golden line id -> the answer that was graded (the last attempt)."""
    saved = json.loads((paths.RESULTS / f"{run_name}.json").read_text())
    return {line["id"]: line["attempts"][-1].get("output", "") for line in saved}


@functools.cache
def scores(run_name: str) -> dict[str, tuple[int, int]]:
    """Slice -> (lines passed, lines in the slice), graded again now. Each run is graded once."""
    passed, total = {}, {}
    for line_id, output in answers(run_name).items():
        golden = GOLDEN[line_id]
        total[golden["slice"]] = total.get(golden["slice"], 0) + 1
        passed[golden["slice"]] = (
            passed.get(golden["slice"], 0) + grade(output, golden["expected"])[0]
        )
    return {s: (passed[s], total[s]) for s in total}


def passes(run_name: str) -> dict[str, bool]:
    """Returns golden line id -> whether the saved answer passes, graded again now."""
    return {i: grade(out, GOLDEN[i]["expected"])[0] for i, out in answers(run_name).items()}


def with_range(run_name: str, slice_name: str) -> str:
    """Returns a score with its exact 95% range, as "14/16 · 62–98%"."""
    passed, total = scores(run_name)[slice_name]
    low, high = exact_interval(passed, total)
    return f"{passed}/{total} · {round(100 * low)}–{round(100 * high)}%"


def paired(first: str, second: str, slices: list[str]) -> list:
    """Returns how two runs differ case by case on these slices, with the exact McNemar p-value."""
    a, b = passes(first), passes(second)
    ids = [i for i in a if GOLDEN[i]["slice"] in slices]
    only_first = sum(a[i] and not b[i] for i in ids)
    only_second = sum(b[i] and not a[i] for i in ids)
    return [only_first, only_second, f"{paired_p_value(only_first, only_second):.2g}"]


def percent(run_name: str, slice_name: str) -> str:
    """Returns a run's score on one slice, as "88%"."""
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
        counts["cycle"] = counts.get("cycle", 0) + ("cycle" in named(reason, PATTERNS))
    return [counts[term] for term in [*TERMS, "cycle"]]


def table(header: list[str], rows: list[list]) -> None:
    """Prints a Markdown table."""
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(str(cell) for cell in row) + " |")
    print()


CLAUDE_RUNS = ["claude-opus-5-5"] + [f"claude-opus-5-5+repeat{n}" for n in (2, 3, 4)]


def decisions(run_name: str) -> dict[str, str]:
    """Returns case id -> the decision the run gave ("?" when the answer has none)."""
    given = {}
    for line_id, output in answers(run_name).items():
        if line_id.endswith("-decision"):
            answer, _ = parse(output)
            given[line_id.removesuffix("-decision")] = str((answer or {}).get("decision", "?"))
    return given


def print_repeats(runs: list[str]) -> None:
    """Prints the same request run several times: the totals, then the cases that changed sides."""
    labels = ["Nov 8"] + [f"rerun {n}" for n in range(1, len(runs))]
    by_run = {r: scores(r) for r in runs}
    table(
        ["", *labels],
        [
            ["normal accounts closed (of 16)"] + [by_run[r]["decision-close"][0] for r in runs],
            ["laundering caught, single scheme (of 10)"]
            + [by_run[r]["decision-escalate-single"][0] for r in runs],
            ["laundering caught, hub (of 6)"]
            + [by_run[r]["decision-escalate-hub"][0] for r in runs],
            ["evidence passed, laundering accounts (of 16)"]
            + [
                by_run[r]["rows-escalate-single"][0] + by_run[r]["rows-escalate-hub"][0]
                for r in runs
            ],
            ["rows cited: laundering / other"]
            + ["{:,} / {:,}".format(*rows_cited(r)) for r in runs],
        ],
    )
    given = {r: decisions(r) for r in runs}
    changed = [case for case in given[runs[0]] if len({given[r][case] for r in runs}) > 1]
    expected = {case: GOLDEN[f"{case}-decision"]["expected"]["value"] for case in changed}
    table(
        ["case", "right answer", *labels],
        [[case, expected[case]] + [given[r][case] for r in runs] for case in sorted(changed)],
    )
    total = len(given[runs[0]])
    print(f"Same decision in every run: {total - len(changed)} of {total} cases.\n")
    for label, run_name in zip(labels[1:], runs[1:], strict=True):
        record = paths.RESULTS / f"{run_name}.meta.json"
        thinking = json.loads(record.read_text())["thinking_tokens_per_case"]
        reasoned = sum(1 for tokens in thinking.values() if tokens)
        per_case = round(sum(thinking.values()) / len(thinking))
        print(
            f"{label}: reasoned on {reasoned} of {len(thinking)} cases, {per_case} tokens per case."
        )
    print()


def print_probe() -> None:
    """Prints which laundering terms each model names when asked directly, if probe.py was run."""
    files = sorted((paths.RESULTS / "probe").glob("*.json"))
    if not files:
        return
    print("## Asked directly: which patterns does each model name?\n")
    rows = []
    for file in files:
        saved = json.loads(file.read_text())
        for answer in saved["answers"]:
            patterns = named(answer["answer"], PATTERNS)
            cash = named(answer["answer"], CASH_TERMS)
            rows.append(
                [
                    saved["model"],
                    answer["question"],
                    f"{len(patterns)} of {len(PATTERNS)}: {', '.join(patterns) or 'none'}",
                    ", ".join(cash) or "none",
                ]
            )
    table(["model", "question", "network patterns named", "cash terms named"], rows)


def main() -> None:
    """Prints every table of the README, then the vocabulary table."""
    print("## What was measured\n")
    runs = [
        "rule",
        "mistral-small-2603",
        "mistral-large-2512",
        "mistral-large-4",
        "claude-opus-5-5",
    ]
    table(
        ["slice", "n"] + runs,
        [[label, scores("rule")[s][1]] + [percent(r, s) for r in runs] for label, s in SLICES],
    )

    print("## Decision scores with their exact 95% ranges\n")
    decision = [(label, s) for label, s in SLICES if s.startswith("decision")]
    table(["slice", *runs], [[label] + [with_range(r, s) for r in runs] for label, s in decision])

    print("## Claude against Large 4, case by case\n")
    table(
        ["slice", "only Claude right", "only Large 4 right", "p (exact McNemar)"],
        [[label, *paired("claude-opus-5-5", "mistral-large-4", [s])] for label, s in SLICES]
        + [
            [
                "decision: escalate, all 16 laundering accounts",
                *paired(
                    "claude-opus-5-5",
                    "mistral-large-4",
                    ["decision-escalate-single", "decision-escalate-hub"],
                ),
            ]
        ],
    )

    print("## Checking the harness (Large 4)\n")
    table(
        ["run", "close", "escalate (single / hub)", "evidence (single / hub)"],
        [
            [
                label,
                percent(r, "decision-close"),
                f"{percent(r, 'decision-escalate-single')} / {percent(r, 'decision-escalate-hub')}",
                f"{percent(r, 'rows-escalate-single')} / {percent(r, 'rows-escalate-hub')}",
            ]
            for label, r in [
                ("JSON mode, temperature 0", "mistral-large-4"),
                ("Claude's schema, temperature 0", "mistral-large-4+schema"),
                ("Claude's schema, temperature 1", "mistral-large-4+schema-temp1"),
            ]
        ],
    )

    print("## Three prompt changes (Small and Large 3)\n")
    rows = []
    for variant in ("", "simulated", "objective", "both"):
        row = [variant or "nothing"]
        for model in ("mistral-small-2603", "mistral-large-2512"):
            r = f"{model}+{variant}" if variant else model
            row += [
                percent(r, "decision-close"),
                f"{percent(r, 'decision-escalate-single')} / {percent(r, 'decision-escalate-hub')}",
                " / ".join(
                    percent(r, s)
                    for s in ("rows-escalate-single", "rows-escalate-hub", "rows-close")
                ),
            ]
        rows.append(row)
    columns = ["close", "escalate (single / hub)", "evidence (single / hub / close)"]
    table(["added"] + [f"Small: {c}" for c in columns] + [f"Large 3: {c}" for c in columns], rows)

    print("## Giving Large 4 Claude's method\n")
    runs = [
        ("Large 4", "mistral-large-4"),
        ("A: + method", "mistral-large-4+method"),
        ("C: + method, neutral alert", "mistral-large-4+method-neutral"),
        ("Claude", "claude-opus-5-5"),
    ]
    by_run = {r: scores(r) for _, r in runs}
    table(
        [""] + [label for label, _ in runs],
        [
            ["normal accounts closed (of 16)"] + [by_run[r]["decision-close"][0] for _, r in runs],
            ["laundering accounts caught (of 16)"]
            + [
                by_run[r]["decision-escalate-single"][0] + by_run[r]["decision-escalate-hub"][0]
                for _, r in runs
            ],
            ["rows cited: laundering / other"]
            + ["{:,} / {:,}".format(*rows_cited(r)) for _, r in runs],
            ["evidence (single / hub)"]
            + [
                f"{percent(r, 'rows-escalate-single')} / {percent(r, 'rows-escalate-hub')}"
                for _, r in runs
            ],
        ],
    )

    print("## Claude Opus 5.5, the same request four times\n")
    print_repeats(CLAUDE_RUNS)

    print_probe()

    print("## The words each run uses (accounts of 32 whose reason contains the term)\n")
    names = sorted(
        p.name[:-5]
        for p in paths.RESULTS.glob("*.json")
        if p.name.count(".") == 1 and p.name != "rule.json"
    )
    table(["run", *TERMS, "cycle or circular"], [[name] + vocabulary(name) for name in names])


if __name__ == "__main__":
    main()
