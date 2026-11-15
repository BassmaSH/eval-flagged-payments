"""The system under test: one flagged account in, the model's JSON answer out.

    system = ModelSystem("mistral-small-2603")
    system("cases/P01.md")
    ->  '{"reason": "...", "decision": "ESCALATE", "rows": ["T003", "T009"]}'

Needs MISTRAL_API_KEY in the environment; a "claude-…" model needs ANTHROPIC_API_KEY instead (added
Nov 8, as an outside reference).

Code written by Claude Code on Nov 8, 2026, reorganised on Nov 15. The call is the author's from Oct
15 (run_cases.py in github.com/BassmaSH/the-data-cant-tell) and the prompt is the author's wording
(docs/NOTEBOOK.md, "Prompt"). The author reviews it.
"""

import os

from mistralai.client import Mistral

from paths import BENCHMARK

# The author's choices: one generic alert for every case; no pattern names; reason before the
# decision; JSON mode.
ALERT = "This account has been flagged for suspicious activity."
# The neutral variant (Nov 11, the author's choice): the same place in the message, without "Alert:"
# or "suspicious", to test whether Large 4 reads the alert itself as evidence (its reasoning did, on
# 10 of the 16 normal accounts).
NEUTRAL = "This account was selected for review."
INSTRUCTION = (
    "You are an analyst in a bank's anti-money-laundering team. Analyze the account's "
    "transactions for possible money laundering and flag the suspicious rows. Then decide: "
    "ESCALATE (send it for investigation) or CLOSE (a false alarm).\n"
    "Answer with a JSON object with exactly three fields, in this order:\n"
    '"reason": one or two sentences on what you saw;\n'
    '"decision": "ESCALATE" or "CLOSE";\n'
    '"rows": the ids of the suspicious rows, for example ["T004", "T017"], or [] if there are none.'
)

# Claude has no JSON mode like Mistral's: the format is forced with a schema (same three fields,
# same order). It also takes no temperature, and decides per request whether to reason first (effort
# left at its default): both go in the memo.
CLAUDE_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "reason": {"type": "string"},
            "decision": {"type": "string", "enum": ["ESCALATE", "CLOSE"]},
            "rows": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["reason", "decision", "rows"],
        "additionalProperties": False,
    },
}

MISTRAL_SCHEMA = {
    "type": "json_schema",  # Mistral's shape for the same schema
    "json_schema": {"name": "triage", "schema": CLAUDE_FORMAT["schema"], "strict": True},
}
CLAUDE_MAX_TOKENS = 16000  # room for the reasoning and the answer


class ModelSystem:
    """One model with one prompt. Call it with a case file to get the model's answer.

    The model is called once per case: the -decision and -rows golden lines grade the same answer.

    Attributes:
        settings: what this system sends, for run.py to save next to the answers.
        usage: case file -> (prompt tokens, completion tokens), filled as cases are answered.
        thinking: case file -> the reasoning chunks of a Mistral reasoning answer, if any.
        thinking_tokens: case file -> the output tokens Claude spent reasoning, as the API reports
            them (part of the completion tokens; the reasoning itself is not returned).
    """

    def __init__(
        self,
        model: str,
        extra: str = "",
        schema: bool = False,
        temperature: float = 0,
        neutral: bool = False,
    ) -> None:
        """Fixes the model and the prompt.

        Args:
            model: the API's model name. "claude…" goes to Anthropic, any other name to Mistral.
            extra: one more paragraph for the instruction (a variant from variants/<name>.txt).
            schema: give a Mistral model Claude's schema instead of JSON mode (the harness check).
            temperature: 0 by default; 1 for the randomness check. Ignored for Claude.
            neutral: replace the alert line with NEUTRAL (the neutral-alert check, Nov 11).
        """
        self.model = model
        self.is_claude = model.startswith("claude")
        self.instruction = f"{INSTRUCTION}\n{extra}" if extra else INSTRUCTION
        self.alert = NEUTRAL if neutral else "Alert: " + ALERT
        self.schema = schema
        self.temperature = temperature
        self.usage: dict[str, tuple[int, int]] = {}
        self.thinking: dict[str, list] = {}
        self.thinking_tokens: dict[str, int] = {}
        self._answers: dict[str, str] = {}
        self._mistral = (
            None if self.is_claude else Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
        )
        self.settings = {
            "model": model,
            "instruction": self.instruction,
            "alert_line": self.alert,
            "response_format": "json_schema" if (schema or self.is_claude) else "json_object",
            # Claude takes no temperature or top_p, and its reasoning effort is not set here: the
            # API's defaults.
            "temperature": None if self.is_claude else temperature,
            "top_p": None if self.is_claude else 1,
        }

    def __call__(self, case_file: str) -> str:
        """Returns the model's answer to one case, as text. An API error is raised, not cached."""
        if case_file not in self._answers:
            user = f"{self.alert}\n\n{(BENCHMARK / case_file).read_text()}"
            ask = self._ask_claude if self.is_claude else self._ask_mistral
            self._answers[case_file] = ask(case_file, user)
        return self._answers[case_file]

    def _ask_mistral(self, case_file: str, user: str) -> str:
        res = self._mistral.chat.complete(
            model=self.model,
            temperature=self.temperature,
            top_p=1,
            messages=[
                {"role": "system", "content": self.instruction},
                {"role": "user", "content": user},
            ],
            response_format=MISTRAL_SCHEMA if self.schema else {"type": "json_object"},
        )
        answer = res.choices[0].message.content
        if not isinstance(
            answer, str
        ):  # a reasoning answer comes in chunks: the reasoning, then the text
            self.thinking[case_file] = [
                c.model_dump() for c in answer if getattr(c, "type", "") != "text"
            ]
            answer = "".join(
                getattr(c, "text", "") for c in answer if getattr(c, "type", "") == "text"
            )
        self.usage[case_file] = (res.usage.prompt_tokens, res.usage.completion_tokens)
        return answer

    def _ask_claude(self, case_file: str, user: str) -> str:
        import anthropic  # only needed for a Claude run

        res = anthropic.Anthropic().messages.create(
            model=self.model,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=self.instruction,
            messages=[{"role": "user", "content": user}],
            output_config={"format": CLAUDE_FORMAT},
        )
        self.usage[case_file] = (res.usage.input_tokens, res.usage.output_tokens)
        details = getattr(res.usage, "output_tokens_details", None)
        if details is not None and getattr(details, "thinking_tokens", None) is not None:
            self.thinking_tokens[case_file] = details.thinking_tokens
        if (
            res.stop_reason != "end_turn"
        ):  # a refusal or a cut-off answer: an infra error, not a wrong answer
            raise RuntimeError(f"stop_reason {res.stop_reason}")
        return next(block.text for block in res.content if block.type == "text")
