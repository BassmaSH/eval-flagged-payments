"""Run golden.jsonl through one system and print the per-slice table, like evals-kit's own __main__.

Written by Claude on Nov 8, 2026, at Bassma's request. Every answer is saved in results/<name>.json, to read the
failures for the memo.

    python run.py rule                    # the ten-line rule, no API call
    python run.py mistral-small-2603      # needs MISTRAL_API_KEY (and .venv/bin/python, for mistralai)
    python run.py mistral-large-2512
    python run.py mistral-small-2603 simulated   # a variant: adds variants/simulated.txt to the instruction,
                                                 # saved as results/mistral-small-2603+simulated.json
    python run.py mistral-large-4 schema         # same prompt, Claude's schema instead of JSON mode
    python run.py mistral-large-4 schema-temp1   # the same, at temperature 1 (normal randomness)
    python run.py claude-opus-5-5 repeat2        # the same run again, saved as results/claude-opus-5-5+repeat2.json
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "evals_kit"))  # a copy of github.com/BassmaSH/evals-kit
from runner import load_golden, run, summarize, format_table, exit_code  # noqa: E402
from aml_graders import grade  # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
variant = sys.argv[2] if len(sys.argv) > 2 else ""
if name == "rule":
    from rule import system
else:
    from system import make_system
    if variant.startswith("repeat"):  # the same run again under its own name, to see how much answers vary
        system = make_system(name)
    elif variant == "schema-temp1":  # the schema run again at temperature 1: normal randomness, as Claude ran
        system = make_system(name, schema=True, temperature=1)
    elif variant == "schema":  # not a sentence: the same prompt, with Claude's schema instead of JSON mode
        system = make_system(name, schema=True)
    else:
        extra = (HERE / "variants" / f"{variant}.txt").read_text().strip() if variant else ""
        system = make_system(name, extra)
model, name = name, f"{name}+{variant}" if variant else name  # the saved file gets the variant's name

results = run(load_golden(HERE / "golden.jsonl"), system, grade=grade)
(HERE / "results").mkdir(exist_ok=True)
(HERE / "results" / f"{name}.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
print(f"## {name}\n")
print(format_table(summarize(results)))
if model != "rule":
    import system as s
    tokens_in = sum(i for (m, _), (i, o) in s.usage.items() if m == model)
    tokens_out = sum(o for (m, _), (i, o) in s.usage.items() if m == model)
    print(f"\n{len(s.usage)} calls, {tokens_in} prompt tokens, {tokens_out} completion tokens")
code = exit_code(results)
print("exit", code)
raise SystemExit(code)
