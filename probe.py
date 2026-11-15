"""Ask a model what it knows about laundering patterns, with no account and no alert.

    python probe.py mistral-large-4 claude-opus-5-5     # two questions per model, a few cents
    python probe.py definitions mistral-large-4         # the second set: define four named patterns

The eval showed that the Mistral models never name a network pattern (fan-out, cycle...) on a case,
and Claude does. This asks directly, to tell two explanations apart: the model does not know these
patterns, or it knows them and the case does not call them up. Neither question names a pattern.

The second set asks the reverse: given the name of each of the four patterns the model did not
bring up, can it define it? It includes one invented name, as a control: a model that defines that
one too is not showing knowledge.

Saves results/probe/<model>.json (first set) or <model>+definitions.json: each question as sent,
the full answer, the date and the tokens.
Saved answers are never replaced. python report.py prints which terms each answer names.

Code written by Claude Code on Nov 15, 2026, for the author. Needs MISTRAL_API_KEY, and
ANTHROPIC_API_KEY for a "claude-…" model.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from paths import RESULTS  # noqa: E402

PROBE = RESULTS / "probe"
DEFINE = "In money laundering through bank transactions, what is a {} pattern?"
QUESTION_SETS = {
    "patterns": {
        "open": "What are the common patterns of money laundering?",
        "network": (
            "What patterns of money laundering can be seen in a network of transactions between "
            "bank accounts?"
        ),
    },
    "definitions": {
        "scatter-gather": DEFINE.format("scatter-gather"),
        "gather-scatter": DEFINE.format("gather-scatter"),
        "bipartite": DEFINE.format("bipartite"),
        "stack": DEFINE.format("stack"),
        "hinge-loop (invented)": DEFINE.format("hinge-loop"),  # the control: no such pattern
    },
}
CLAUDE_MAX_TOKENS = 16000


def ask_mistral(model: str, question: str) -> tuple[str, list[int]]:
    """Returns a Mistral model's answer and its (prompt, completion) tokens, at temperature 0."""
    from mistralai.client import Mistral

    client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
    res = client.chat.complete(
        model=model, temperature=0, top_p=1, messages=[{"role": "user", "content": question}]
    )
    answer = res.choices[0].message.content
    if not isinstance(answer, str):  # a reasoning answer comes in chunks: keep the text
        answer = "".join(getattr(c, "text", "") for c in answer if getattr(c, "type", "") == "text")
    return answer, [res.usage.prompt_tokens, res.usage.completion_tokens]


def ask_claude(model: str, question: str) -> tuple[str, list[int]]:
    """Returns a Claude model's answer and its (prompt, completion) tokens, at API defaults."""
    import anthropic

    res = anthropic.Anthropic().messages.create(
        model=model, max_tokens=CLAUDE_MAX_TOKENS, messages=[{"role": "user", "content": question}]
    )
    answer = "".join(block.text for block in res.content if block.type == "text")
    return answer, [res.usage.input_tokens, res.usage.output_tokens]


def main(argv: list[str]) -> None:
    """Asks each model one set of questions and saves its answers, one file per model and set."""
    set_name = argv[0] if argv and argv[0] in QUESTION_SETS else "patterns"
    models = argv[1:] if argv and argv[0] in QUESTION_SETS else argv
    if not models:
        sys.exit(__doc__)
    PROBE.mkdir(parents=True, exist_ok=True)
    suffix = "" if set_name == "patterns" else f"+{set_name}"
    for model in models:
        path = PROBE / f"{model}{suffix}.json"
        if path.exists():
            sys.exit(f"results/probe/{path.name} already exists and is not replaced.")
        ask = ask_claude if model.startswith("claude") else ask_mistral
        answers = []
        for name, question in QUESTION_SETS[set_name].items():
            answer, tokens = ask(model, question)
            answers.append({"question": name, "sent": question, "answer": answer, "tokens": tokens})
            print(f"{model}, {name}: {len(answer)} characters")
        record = {
            "model": model,
            "questions": set_name,
            "date": datetime.now().isoformat(timespec="seconds"),
        }
        path.write_text(json.dumps({**record, "answers": answers}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
