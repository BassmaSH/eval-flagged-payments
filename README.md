# Can a model take false alarms off an anti-money-laundering analyst?

*Bassma Saissi Hassani, November 2026. A small benchmark built in a weekend, in a field new to me: 32 flagged
accounts from IBM's synthetic bank, a rule baseline, three Mistral models and Claude Opus 5.5 as an outside
reference. This page is the memo; `NOTEBOOK.md` is the record, with every prediction written before its run.*

**The decision.** Whether to put a language model in front of the alert queue: it would close the clear false
alarms and pass the rest to an analyst, with the transactions that matter.

**The answer.** Not with the Mistral models as tested. On simulated alerts, all three (Small 4, Large 3 and the
newest, Large 4) escalated every account: they closed 0 of 16 false alarms, so they saved the analyst no time.
Telling them the bank is simulated, or that closing false alarms is the goal, did not fix it. Claude Opus 5.5, run
once on the same cases, closed 14 of 16 and still caught 11 of 16 laundering accounts. It read regular payments as
routine and flagged the one-off payments inside them, which is how the laundering looks in this data, and what I
only saw myself after being shown the answers. So the task can be done from one account, and the gap is on the
model side: giving Large 4 Claude's exact answer format, then normal randomness, changed nothing. It might be the
model, but I can't conclude on data: Claude might also have seen descriptions of this
public dataset before, and it ran once, not at temperature 0. This is a gap to report, not a weakness to hide, but I
would still test it on better data before deciding anything.

## What was measured

32 flagged accounts from IBM's synthetic bank (Sep 1–18, 2022): 16 laundering, 16 normal accounts picked because
they look suspicious. The model sees one account's transactions and a generic alert, and answers in JSON: a reason,
ESCALATE or CLOSE, and the ids of the suspicious rows. Two scores per account: the **decision**, and the
**evidence** (more than half of the laundering rows cited and no normal row; for a normal account, no row cited).

Runs of Nov 8, 2026, same prompt for every model; answers in `results/`.

| slice | n | rule (no model) | `mistral-small-2603` | `mistral-large-2512` | `mistral-large-4` | `claude-opus-5-5` |
|---|---|---|---|---|---|---|
| decision: escalate, single scheme | 10 | 30% | 100% | 100% | 100% | 80% |
| decision: escalate, hub account | 6 | 17% | 100% | 100% | 100% | 50% |
| **decision: close (the time saved)** | 16 | **94%** | **0%** | **0%** | **0%** | **88%** |
| evidence: escalate, single scheme | 10 | 10% | 0% | 10% | 0% | 20% |
| evidence: escalate, hub account | 6 | 0% | 0% | 0% | 0% | 17% |
| evidence: close | 16 | 94% | 0% | 0% | 0% | 88% |

Settings: the Mistral models at temperature 0 in JSON mode. Claude takes no temperature setting and always reasons
first (left at its default level), and its format was forced with a schema; it ran once. Large 4 also reasons
before answering (about 4,200 output tokens per case, against about 500 for Claude).

**A human:** 0 of 4 decisions right on four blind cases, in 7 minutes, before learning what this data looks like.

The rule escalates an account that paid 8 or more different accounts within 3 days. A model that always says
ESCALATE scores 100% on the escalate slices and 0% on close: the three Mistral models scored exactly that. The rule
fails the other way: it closes almost everything, laundering included, so it is a floor.

## Checking the harness: is it the model, or what surrounds it?

Claude's run did not have exactly the Mistral setup: its format was forced by a schema, it ran with normal
randomness, and it reasons before answering. Large 4 already reasons by default, so it was rerun with Claude's
schema (one change), then the same at temperature 1 (one more change). Prediction for the first: "same perf this
run with temp 0".

| Large 4 run | close | escalate (single / hub) | evidence (single / hub) | output tokens |
|---|---|---|---|---|
| JSON mode, temperature 0 | 0% | 100% / 100% | 0% / 0% | 134,706 |
| Claude's schema, temperature 0 | 0% | 100% / 100% | 0% / 0% | 142,781 |
| Claude's schema, temperature 1 | 0% | 100% / 100% | 10% / 0% | 138,796 |

Neither the format nor randomness explains the gap. What remains is the model, and two things not checked: whether
Claude's 88% holds on a rerun, and whether the wording of the instruction, drafted with Claude's help, suits Claude
better.

## Checking the cause: three prompt changes (Mistral)

Each change was one or two sentences added to the instruction, written with a prediction before the run, on all 32
cases (a close-only rerun could not tell a model that reads the data correctly from one that now closes everything).
The bar for "it works", set before the last run: close goes up, escalate stays near 100%, and evidence rises.

| added to the instruction | Small: close | Small: escalate (single / hub) | Large 3: close | Large 3: escalate | evidence |
|---|---|---|---|---|---|
| nothing (the table above) | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 P04 only |
| "simulated bank… regular payments of the same amount to the same accounts are normal" | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 0% (lost P04) |
| "your objective is to close false alarms… and to escalate real cases" | 6% | 90% / 67% | 0% | 100% / 100% | unchanged |
| both sentences | **69%** | **40% / 33%** | 0% | 100% / 100% | unchanged |

My predictions were wrong twice ("close around 90%, escalate around 80%"); the third ("as bad as the last run") held
for Large 3. No change met the bar: the evidence score never rose.

## Where the Mistral models fail

They read **regularity as laundering**. On P17, a normal account, Mistral Large 3 wrote: "multiple repeated
transactions with identical amounts to the same counterparties… suggest potential layering activity", and cited
42 of its 59 rows (Small cited 30). In this simulated bank, ordinary customers repeat identical payments every day.
"Structuring" (splitting money into repeated payments to stay under reporting limits) is a real-world red flag,
applied to a world where it means nothing. I made the same mistake on my own blind cases. Large 4, with all its
reasoning, called every normal account "classic structuring".

Told that regularity is normal, they keep it: Small on P31, with the sentence in its prompt, called the same
repetition "unusual for regular customer behavior". With both sentences, Small turned it around and closed laundering
accounts with "regular payments… suggest normal customer behavior", escalating on very large amounts instead. The
feature changed; the method did not.

On the evidence, they cite the busy, regular rows and miss the two or three quiet laundering rows: Large 3 passed one
case (P04, two foreign-currency payments after self-transfers), in three of the four runs.

## What Claude did differently

It called the regular payments "routine recurring payments" and escalated on one-off items inside them: a burst of
credits from new counterparties (P06, P08), a self-conversion followed by a payout in another currency (P03, P04,
P10, P13), three payments within minutes in three formats (P09, P12). It missed the two cycles with only two quiet
rows each (P01, P02) and three hub accounts (P11, P14, P16), whose two-way flows it read as "related-entity treasury
transfers". It wrongly escalated P28 ("just under a 10k threshold", the real-world habit again) and P32 (a one-off
cheque from a new counterparty, then three fast payments). Its evidence is still weak: it often finds the right
area but cites fewer than half of the laundering rows.

## What next, and what it costs

1. **Check that Claude's result holds** (under $1 a run, not done for lack of credits): the same 32 cases three to
   five times, to see how stable its decisions are without temperature 0; then fresh accounts it cannot have seen. New accounts from another of
   IBM's datasets reduce the risk only partly, since those are public too; regenerated or real data removes it.
2. **Better data:** IBM's larger datasets cover a longer period, so a monthly rhythm becomes visible; then a sample
   of anonymised alerts from one bank, with an analyst's decisions as the key. That is the only test of real
   capacity.
3. **For the Mistral models:** describe the pattern in the prompt (one-off payments inside a regular account) and
   test it on new cases, not these 32. The prompt changes above already tuned on these cases; a fourth would fit
   this simulator, not the task.

## Limits

- **Synthetic data:** no real bank or person; the simulator has habits a bank does not (daily identical payments,
  `Reinvestment` transfers to self, very large amounts).
- **Public data:** IBM's dataset has been public since 2023; any model may have read descriptions of how it behaves.
- **One account, 18 days:** an analyst's best signals (a monthly rhythm, the other accounts in the scheme) are out of
  reach. From inside one account, a scatter-gather looks exactly like a fan-out.
- **32 cases, one run per prompt:** each close case is 6 points on its slice. The three prompt changes were tested
  on the same 32 cases. The Mistral runs are at temperature 0; Claude's single run is not, so its scores could move
  on a rerun.
- **Not identical settings:** in the main table Claude's format was forced by a schema, the Mistral models' by JSON
  mode; Claude and Large 4 reason before answering, Small 4 and Large 3 do not. Large 4 was rerun with Claude's schema
  and at temperature 1 (no change). The instruction was drafted with Claude's help, which may suit Claude.
- **Hand-picked cases:** the normal accounts were chosen to look suspicious, which is realistic for an alert queue
  but not a random sample. The rule's thresholds are an example, not a bank's rules.
- **Cost:** about 103,000 prompt tokens per run (about 3,200 per case: tables of ids and amounts cost more tokens
  than prose). Eight runs of Small 4 and Large 3, a few cents each. Large 4: 73,355 prompt and 134,706 completion
  tokens, about $0.33; its two harness reruns about $0.35 each. Claude Opus 5.5: 103,549 prompt and 16,455
  completion tokens, about $0.74.

## Run it

```bash
python run.py rule                      # the rule baseline, no API call, standard library only
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export MISTRAL_API_KEY=...              # and ANTHROPIC_API_KEY for a Claude model
.venv/bin/python run.py mistral-small-2603
.venv/bin/python run.py mistral-small-2603 both      # a prompt variant from variants/
.venv/bin/python run.py mistral-large-4 schema       # the harness check
```

Each run prints the per-slice table and saves every answer in `results/`. `golden.jsonl` holds two lines per
case (the decision and the evidence), built by `make_golden.py` from `cases/` and `keys/`; `aml_graders.py` scores
them. The runner in `evals_kit/` is a copy of [evals-kit](https://github.com/BassmaSH/evals-kit).

## The data

IBM's synthetic anti-money-laundering data, split HI-Small (Altman et al., *Realistic Synthetic Financial
Transactions for Anti-Money Laundering Models*, NeurIPS 2023, <https://arxiv.org/abs/2306.16424>), licence
CDLA-Sharing-1.0. Everything is simulated: no real person or bank. The raw files are not in this repository;
`prep/README.md` says how to rebuild them, and `make_case.py` cuts a case from them. The files derived from that
data (`cases/`, `keys/`, `golden.jsonl`) are shared under the same CDLA-Sharing-1.0 licence; the code is MIT.

## How this was built

I read the field, wrote the question, chose the cases and the slices, set the scoring rule and the prompt, made a
prediction before each run and decided what the results mean. Claude (Claude Code) wrote the scripts from those
choices (case building, graders, the rule file, the runner script and the model client), read the models' reasons
in `results/`, kept the record in `NOTEBOOK.md`, and drafted this memo from my notes.
