"""Run golden.jsonl through one system and print the per-slice table, like evals-kit's own __main__.

Code written by Claude Code on Nov 8, 2026, for the author; reorganised on Nov 15 (the variants in one table, a
main() function). Every answer is saved in results/<name>.json, to read the failures for the memo. A model run
also saves results/<name>.meta.json: the settings, the prompt as sent, the date, the library versions and the
tokens per case.

Saved answers are never replaced: to run something again, add repeat2, repeat3, ... as the last word.

    python run.py rule                    # the ten-line rule, no API call
    python run.py mistral-small-2603      # needs MISTRAL_API_KEY (and .venv/bin/python, for mistralai)
    python run.py mistral-large-2512
    python run.py mistral-small-2603 simulated   # a variant from the VARIANTS table below,
                                                 # saved as results/mistral-small-2603+simulated.json
    python run.py mistral-large-4 schema         # same prompt, Claude's schema instead of JSON mode
    python run.py mistral-large-4 method-neutral # the method, and "This account was selected for review." as alert
    python run.py claude-opus-5-5 repeat2        # the same run again, saved as results/claude-opus-5-5+repeat2.json
    python run.py mistral-large-4 method repeat2 # a variant again, saved as …+method+repeat2.json
"""
import json
import platform
import subprocess
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "evals_kit"))  # a copy of github.com/BassmaSH/evals-kit
from runner import load_golden, run, summarize, format_table, exit_code  # noqa: E402
from aml_graders import grade  # noqa: E402

# Every variant that was run: its name on the command line -> what it changes in the call.
#   extra:       a paragraph added to the instruction, read from variants/<extra>.txt
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


def read_arguments(argv):
    """['mistral-large-4', 'method', 'repeat2'] -> ('mistral-large-4', 'method', 'repeat2').
    The variant and the repeat are both optional. A repeat changes nothing in the call: it only gives the run its
    own file name, to see how much the answers vary from one run to the next."""
    if not argv:
        sys.exit(__doc__)
    model, words = argv[0], argv[1:]
    repeat = words.pop() if words and words[-1].startswith("repeat") else ""
    variant = words[0] if words else ""
    if len(words) > 1 or variant not in VARIANTS:
        sys.exit(f"unknown variant {' '.join(words)!r}. Known: {', '.join(v for v in VARIANTS if v)}")
    return model, variant, repeat


def variant_settings(variant):
    """The table row, with the file name under "extra" replaced by the paragraph it holds."""
    settings = dict(VARIANTS[variant])
    if "extra" in settings:
        settings["extra"] = (HERE / "variants" / f"{settings['extra']}.txt").read_text().strip()
    return settings


def code_version():
    def git(*args):
        return subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True).stdout.strip()
    return git("rev-parse", "--short", "HEAD") + (" + uncommitted changes" if git("status", "--porcelain") else "")


def library_versions():
    versions = {}
    for library in ("mistralai", "anthropic"):
        try:
            versions[library] = metadata.version(library)
        except metadata.PackageNotFoundError:
            pass
    return versions


def main(argv):
    model, variant, repeat = read_arguments(argv)
    run_name = "+".join(part for part in (model, variant, repeat) if part)  # the name of the saved files
    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)
    # Checked before any model call: a rerun never replaces saved answers (the rule gives the same file each time).
    if model != "rule" and (results_dir / f"{run_name}.json").exists():
        base = "+".join(part for part in (model, variant) if part)
        free = next(n for n in range(2, 1000) if not (results_dir / f"{base}+repeat{n}.json").exists())
        again = " ".join(part for part in (model, variant, f"repeat{free}") if part)
        sys.exit(f"results/{run_name}.json already exists and is not replaced. "
                 f"To run it again under a new name: python run.py {again}")

    if model == "rule":
        if variant or repeat:
            sys.exit("the rule takes no variant")
        from rule import system as answer_case
    else:
        from system import ModelSystem  # needs mistralai, which the rule does not
        answer_case = ModelSystem(model, **variant_settings(variant))

    # One attempt: the model is called once per case and both lines grade that answer (system.py's cache),
    # so a second attempt would only grade the same answer again.
    results = run(load_golden(HERE / "golden.jsonl"), answer_case, grade=grade, max_attempts=1)
    (results_dir / f"{run_name}.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"## {run_name}\n")
    print(format_table(summarize(results)))

    if model != "rule":
        usage, thinking = answer_case.usage, answer_case.thinking
        tokens_in = sum(prompt for prompt, _ in usage.values())
        tokens_out = sum(completion for _, completion in usage.values())
        print(f"\n{len(usage)} calls, {tokens_in} prompt tokens, {tokens_out} completion tokens")
        meta = {"run": run_name, "date": datetime.now().isoformat(timespec="seconds"),
                "code_commit": code_version(), "python": platform.python_version(),
                "libraries": library_versions(), "settings": answer_case.settings,
                "calls": len(usage), "prompt_tokens": tokens_in, "completion_tokens": tokens_out,
                "tokens_per_case": {case: list(tokens) for case, tokens in usage.items()}}
        (results_dir / f"{run_name}.meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
        if thinking:  # the reasoning, next to the answers (Nov 11)
            (results_dir / f"{run_name}.thinking.json").write_text(
                json.dumps(thinking, indent=1, ensure_ascii=False))

    code = exit_code(results)
    print("exit", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
