"""Run golden.jsonl through one system and print the per-slice table, like evals-kit's own __main__.

Code written by Claude Code on Nov 8, 2026, for the author; reorganised on Nov 15 (the variants in
one table, a main() function). Every answer is saved in results/<name>.json, to read the failures
for the memo. A model run also saves results/<name>.meta.json: the settings, the prompt as sent, the
date, the library versions and the tokens per case.

Saved answers are never replaced: to run something again, add repeat2, repeat3, ... as the last
word.

    python run.py rule                    # the ten-line rule, no API call
    python run.py mistral-small-2603      # needs MISTRAL_API_KEY and the mistralai library
    python run.py mistral-large-2512
    python run.py mistral-small-2603 simulated   # a variant from the VARIANTS table below,
                                                 # saved as …/mistral-small-2603+simulated.json
    python run.py mistral-large-4 schema         # same prompt, Claude's schema instead of JSON mode
    python run.py mistral-large-4 method-neutral # the method, with the neutral alert line
    python run.py claude-opus-5-5 repeat2        # the same run again, saved as …+repeat2.json
    python run.py mistral-large-4 method repeat2 # a variant again, saved as …+method+repeat2.json
"""

import contextlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

SRC = Path(__file__).parent / "src"
# evals_kit is a copy of github.com/BassmaSH/evals-kit
sys.path[:0] = [str(SRC), str(SRC / "evals_kit")]
if TYPE_CHECKING:  # for the type hint only: importing system needs mistralai
    from system import ModelSystem
from runner import exit_code, format_table, load_golden, run_case, summarize  # noqa: E402

import checkpoint  # noqa: E402
from aml_graders import grade  # noqa: E402
from paths import GOLDEN, RESULTS, ROOT, VARIANTS_DIR  # noqa: E402

# Every variant that was run: its name on the command line -> what it changes in the call.
#   extra:       a paragraph added to the instruction, read from src/variants/<extra>.txt
#   schema:      give a Mistral model Claude's schema instead of JSON mode
#   temperature: 0 unless said otherwise
#   neutral:     "This account was selected for review." in place of the alert line
# A new variant is one new line here.
VARIANTS = {
    "": {},  # the plain run
    "simulated": {"extra": "simulated"},
    "objective": {"extra": "objective"},
    "both": {"extra": "both"},
    "method": {"extra": "method"},
    "schema": {"schema": True},
    "schema-temp1": {"schema": True, "temperature": 1},  # normal randomness, as Claude ran
    "method-neutral": {"extra": "method", "neutral": True},
}


def read_arguments(argv: list[str]) -> tuple[str, str, str]:
    """Returns (model, variant, repeat) from the words typed after run.py.

    ['mistral-large-4', 'method', 'repeat2'] -> ('mistral-large-4', 'method', 'repeat2'). The
    variant and the repeat are both optional. A repeat changes nothing in the call: it only gives
    the run its own file name, to see how much the answers vary from one run to the next.
    """
    if not argv:
        sys.exit(__doc__)
    model, words = argv[0], argv[1:]
    repeat = words.pop() if words and words[-1].startswith("repeat") else ""
    variant = words[0] if words else ""
    if len(words) > 1 or variant not in VARIANTS:
        sys.exit(
            f"unknown variant {' '.join(words)!r}. Known: {', '.join(v for v in VARIANTS if v)}"
        )
    return model, variant, repeat


def variant_settings(variant: str) -> dict:
    """The table row, with the file name under "extra" replaced by the paragraph it holds."""
    settings = dict(VARIANTS[variant])
    if "extra" in settings:
        settings["extra"] = (VARIANTS_DIR / f"{settings['extra']}.txt").read_text().strip()
    return settings


def code_version() -> str:
    """The commit the code is at, and whether files were changed since."""

    def git(*args: str) -> str:
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return done.stdout.strip()

    changed = " + uncommitted changes" if git("status", "--porcelain") else ""
    return git("rev-parse", "--short", "HEAD") + changed


def library_versions() -> dict[str, str]:
    """The installed versions of the two model libraries."""
    versions = {}
    for library in ("mistralai", "anthropic"):
        with contextlib.suppress(metadata.PackageNotFoundError):  # not installed: left out
            versions[library] = metadata.version(library)
    return versions


def refuse_to_replace(model: str, variant: str, run_name: str) -> None:
    """Stops, before any model call, when this run's answers are already saved.

    The message names the next free repeat.
    """
    if not (RESULTS / f"{run_name}.json").exists():
        return
    base = "+".join(part for part in (model, variant) if part)
    free = next(n for n in range(2, 1000) if not (RESULTS / f"{base}+repeat{n}.json").exists())
    again = " ".join(part for part in (model, variant, f"repeat{free}") if part)
    sys.exit(
        f"results/{run_name}.json already exists and is not replaced. "
        f"To run it again under a new name: python run.py {again}"
    )


def run_record(run_name: str, model_system: "ModelSystem") -> dict:
    """Returns how a model run was made.

    The settings, the prompt as sent, the date, the versions and the tokens per case.
    """
    usage = model_system.usage
    return {
        "run": run_name,
        "date": datetime.now().isoformat(timespec="seconds"),
        "code_commit": code_version(),
        "python": platform.python_version(),
        "libraries": library_versions(),
        "settings": model_system.settings,
        "calls": len(usage),
        "prompt_tokens": sum(prompt for prompt, _ in usage.values()),
        "completion_tokens": sum(completion for _, completion in usage.values()),
        "tokens_per_case": {case: list(tokens) for case, tokens in usage.items()},
        "thinking_tokens_per_case": model_system.thinking_tokens,
    }


def save_json(name: str, content: object) -> None:
    """Writes content as JSON in results/."""
    (RESULTS / name).write_text(json.dumps(content, indent=1, ensure_ascii=False))


def run_and_save(cases: list[dict], answer_case: object, run_name: str) -> list[dict]:
    """Runs every golden line, writing the results so far after each one.

    A run that stopped (a closed terminal) or whose calls failed (no credit left) leaves
    results/<run>.partial.json and no final file. The same command then resumes it: the cases
    already answered in full are not asked again, the others are.
    """
    partial = RESULTS / f"{run_name}.partial.json"
    kept = checkpoint.resume(partial, cases, answer_case)
    if kept:
        print(f"resuming {run_name}: {len(kept)} of {len(cases)} lines already answered")
    results = []
    for case in cases:
        # One attempt: the model is called once per case and both lines grade that answer
        # (system.py's cache), so a second attempt would only grade the same answer again.
        results.append(kept.get(case["id"]) or run_case(case, answer_case, grade, max_attempts=1))
        checkpoint.save(partial, results, answer_case)
    failed = sum(result["status"] == "infra_error" for result in results)
    if failed:
        print(f"{failed} of {len(results)} lines got no answer: the run is not saved as finished.")
        print("Run the same command again to ask only the missing cases.")
    else:
        save_json(f"{run_name}.json", results)
        partial.unlink()
    return results


def main(argv: list[str]) -> int:
    """Runs one system on golden.jsonl, saves its answers and prints the table.

    Returns:
        The exit code: 0, or 2 when a call or a grader crashed.
    """
    model, variant, repeat = read_arguments(argv)
    run_name = "+".join(
        part for part in (model, variant, repeat) if part
    )  # the name of the saved files
    RESULTS.mkdir(exist_ok=True)

    if (
        model == "rule"
    ):  # no variant, and it may replace its file: it gives the same answers every time
        if variant or repeat:
            sys.exit("the rule takes no variant")
        from rule import system as answer_case
    else:
        refuse_to_replace(model, variant, run_name)
        from system import ModelSystem  # needs mistralai, which the rule does not

        answer_case = ModelSystem(model, **variant_settings(variant))

    results = run_and_save(load_golden(GOLDEN), answer_case, run_name)
    print(f"## {run_name}\n")
    print(format_table(summarize(results)))

    finished = (RESULTS / f"{run_name}.json").exists() and not (
        RESULTS / f"{run_name}.partial.json"
    ).exists()
    if model != "rule" and finished:
        record = run_record(run_name, answer_case)
        save_json(f"{run_name}.meta.json", record)
        if answer_case.thinking:  # the reasoning, next to the answers (Nov 11)
            save_json(f"{run_name}.thinking.json", answer_case.thinking)
        print(
            f"\n{record['calls']} calls, {record['prompt_tokens']} prompt tokens, "
            f"{record['completion_tokens']} completion tokens"
        )

    code = exit_code(results)
    print("exit", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
