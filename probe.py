"""Ask a model what it knows about laundering patterns, with no account and no alert.

    python probe.py mistral-large-4 claude-opus-5-5     # two questions per model, a few cents

The eval showed that the Mistral models never name a network pattern (fan-out, cycle...) on a case,
and Claude does. This asks directly, to tell two explanations apart: the model does not know these
patterns, or it knows them and the case does not call them up. Neither question names a pattern.

Saves results/probe/<model>.json: each question as sent, the full answer, the date and the tokens.
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
QUESTIONS = {
    "open": "What are the common patterns of money laundering?",
    "network": (
        "What patterns of money laundering can be seen in a network of transactions between bank "
        "accounts?"
    ),
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


def main(models: list[str]) -> None:
    """Asks each model the questions and saves its answers, one file per model."""
    if not models:
        sys.exit(__doc__)
    PROBE.mkdir(parents=True, exist_ok=True)
    for model in models:
        path = PROBE / f"{model}.json"
        if path.exists():
            sys.exit(f"results/probe/{model}.json already exists and is not replaced.")
        ask = ask_claude if model.startswith("claude") else ask_mistral
        answers = []
        for name, question in QUESTIONS.items():
            answer, tokens = ask(model, question)
            answers.append({"question": name, "sent": question, "answer": answer, "tokens": tokens})
            print(f"{model}, {name}: {len(answer)} characters")
        record = {"model": model, "date": datetime.now().isoformat(timespec="seconds")}
        path.write_text(json.dumps({**record, "answers": answers}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
