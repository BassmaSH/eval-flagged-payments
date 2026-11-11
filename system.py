"""The system under test: one flagged account in, the model's JSON answer out.

Written by Claude on Nov 8, 2026, at Bassma's request; the call is hers from Oct 15
(run_cases.py in github.com/BassmaSH/the-data-cant-tell), the prompt is her wording (NOTEBOOK.md, "Prompt"). She reviews it.

    system = make_system("mistral-small-2603")
    system("cases/P01.md")  ->  '{"reason": "...", "decision": "ESCALATE", "rows": ["T003", "T009"]}'

Needs MISTRAL_API_KEY in the environment; a "claude-…" model needs ANTHROPIC_API_KEY instead (added Nov 8, her
request, as an outside reference).
"""
import os
from pathlib import Path

from mistralai.client import Mistral

HERE = Path(__file__).parent

# Her choices: one generic alert for every case; no pattern names; reason before the decision; JSON mode.
ALERT = "This account has been flagged for suspicious activity."
# The neutral variant (Nov 11, her choice): the same place in the message, without "Alert:" or "suspicious", to test
# whether Large 4 reads the alert itself as evidence (its reasoning did, on 10 of the 16 normal accounts).
NEUTRAL = "This account was selected for review."
INSTRUCTION = (
    "You are an analyst in a bank's anti-money-laundering team. Analyze the account's transactions for possible "
    "money laundering and flag the suspicious rows. Then decide: ESCALATE (send it for investigation) or CLOSE "
    "(a false alarm).\n"
    "Answer with a JSON object with exactly three fields, in this order:\n"
    '"reason": one or two sentences on what you saw;\n'
    '"decision": "ESCALATE" or "CLOSE";\n'
    '"rows": the ids of the suspicious rows, for example ["T004", "T017"], or [] if there are none.'
)

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
# Claude has no JSON mode like Mistral's: the format is forced with a schema (same three fields, in her order).
# It also takes no temperature, and always reasons first (effort left at its default): both go in the memo.
CLAUDE_FORMAT = {"type": "json_schema", "schema": {
    "type": "object",
    "properties": {"reason": {"type": "string"},
                   "decision": {"type": "string", "enum": ["ESCALATE", "CLOSE"]},
                   "rows": {"type": "array", "items": {"type": "string"}}},
    "required": ["reason", "decision", "rows"],
    "additionalProperties": False}}

MISTRAL_SCHEMA = {"type": "json_schema",  # Mistral's shape for the same schema
                  "json_schema": {"name": "triage", "schema": CLAUDE_FORMAT["schema"], "strict": True}}

usage = {}  # (model, input) -> (prompt tokens, completion tokens), for the memo's cost line
thinking = {}  # (model, input) -> the reasoning chunks of a Mistral reasoning answer (none before Nov 11)


def make_system(model, extra="", schema=False, temperature=0, neutral=False):
    """extra: one more paragraph for the instruction, for a named variant run (variants/<name>.txt).
    schema: give a Mistral model Claude's schema instead of JSON mode (the harness check, Nov 9).
    temperature: 0 by default; 1, normal randomness, for the randomness check.
    neutral: replace the alert line with NEUTRAL (the neutral-alert check, Nov 11)."""
    instruction = f"{INSTRUCTION}\n{extra}" if extra else INSTRUCTION
    cache = {}  # one call per case: the -decision and -rows lines grade the same answer

    def system(input):
        if input in cache:
            return cache[input]
        case = (HERE / input).read_text()
        messages = [{"role": "system", "content": instruction},
                    {"role": "user", "content": f"{NEUTRAL if neutral else 'Alert: ' + ALERT}\n\n{case}"}]
        if model.startswith("claude"):
            answer = claude_call(model, instruction, messages[1]["content"], input)
        else:
            res = client.chat.complete(model=model, temperature=temperature, top_p=1, messages=messages,
                                       response_format=MISTRAL_SCHEMA if schema else {"type": "json_object"})
            answer = res.choices[0].message.content
            if not isinstance(answer, str):  # reasoning answers come in chunks: keep the text (as on Oct 15)
                # and, since Nov 11, the reasoning chunks too, to read how it got there (run.py saves them)
                thinking[(model, input)] = [c.model_dump() for c in answer if getattr(c, "type", "") != "text"]
                answer = "".join(getattr(c, "text", "") for c in answer if getattr(c, "type", "") == "text")
            usage[(model, input)] = (res.usage.prompt_tokens, res.usage.completion_tokens)
        cache[input] = answer  # only a call that returned is cached; an exception goes back to the runner
        return answer

    return system


def claude_call(model, instruction, user, input):
    import anthropic  # only needed for a Claude run
    res = anthropic.Anthropic().messages.create(model=model, max_tokens=16000, system=instruction,
                                                messages=[{"role": "user", "content": user}],
                                                output_config={"format": CLAUDE_FORMAT})
    usage[(model, input)] = (res.usage.input_tokens, res.usage.output_tokens)
    if res.stop_reason != "end_turn":  # a refusal or a cut-off answer: an infra error, not a wrong answer
        raise RuntimeError(f"stop_reason {res.stop_reason}")
    return next(b.text for b in res.content if b.type == "text")
