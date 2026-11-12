# Can a language model reduce the number of false positives in AML alert queues?

*This is a summary of a very small benchmark we ran over a weekend: 32 flagged accounts from IBM's synthetic bank, a
rule baseline, three Mistral models, and Claude Opus 5.5 as an external reference. The full record is in
[`NOTEBOOK.md`](NOTEBOOK.md), with each prediction logged prior to running.*

**The decision.** Whether to put a language model in front of the alert queue. It would filter out clear false
alarms and pass the rest to an analyst, along with the transactions that actually mattered.

**The result.** The Mistral models, as tested, did not reduce false positives. On simulated alerts, all three (Small
4, Large 3, and Large 4) escalated every account and closed none of the 16 false alarms. Adjusting the prompt to
specify that the bank is simulated, or that the goal is to close false alarms, did not improve results. For
comparison, we tested Claude Opus 5.5 once on the same cases: it closed 14 of 16 false alarms and still caught 11 of
16 laundering accounts. It interpreted regular payments as routine and flagged the one-off payments inside them,
which is how laundering looks in this dataset, an insight we only recognized after reviewing the answers. This shows
the task can be performed from a single account, and that the gap lies with the models.

We then ran Large 4 again to pinpoint the source of the gap. Giving it Claude's answer format, then normal
randomness, changed nothing. Reading the two models' reasoning side by side, we noticed that Claude started by
describing what an account normally does before identifying unusual transactions. We described this method in Large
4's prompt: it altered its approach but not its decisions. Its reasoning kept coming back to the alert saying the
account had been flagged. We removed the alert as a last trial, and it leaned on the next part of the request that
suggested something was there to find: the instruction to "flag the suspicious rows". For training, this points to
the weight the model gives to what a request takes for granted, not to how it reads the data.

While differences between models are likely, we cannot rule out data familiarity; Claude may have previously
encountered this public dataset. Additionally, Claude was tested only once and not at temperature 0. More testing
on more realistic data is definitely required before we can come to any firm conclusions.

## What was measured

32 flagged accounts from IBM's synthetic bank (Sep 1–18, 2022): 16 laundering, 16 normal (8 drawn at random, 8 chosen from 15 candidates because they look most like an alert). The model sees the transactions on one account and a generic alert and then responds in JSON
format with a reason, an ESCALATE or a CLOSE and the IDs of the suspicious rows. Two scores per account: the
**decision** and the **evidence** (for a laundering account more than half of the laundering rows cited and no
normal row; for a normal account no row is cited).

Runs of 8th November 2026, same prompt for each model; answers in `results/`.

| slice | n | rule (no model) | `mistral-small-2603` | `mistral-large-2512` | `mistral-large-4` | `claude-opus-5-5` |
|---|---|---|---|---|---|---|
| decision: escalate, single scheme | 10 | 30% | 100% | 100% | 100% | 80% |
| decision: escalate, hub account | 6 | 17% | 100% | 100% | 100% | 50% |
| **decision: close (the time saved)** | 16 | **94%** | **0%** | **0%** | **0%** | **88%** |
| evidence: escalate, single scheme | 10 | 10% | 0% | 10% | 0% | 20% |
| evidence: escalate, hub account | 6 | 0% | 0% | 0% | 0% | 17% |
| evidence: close | 16 | 94% | 0% | 0% | 0% | 88% |

Settings: the Mistral models at temperature 0 in JSON mode. Claude takes no temperature setting, always reasons
first (left at its default level), and its format was forced with a schema; it ran once. Large 4 also reasons before
answering (about 4,200 output tokens per case, against about 500 for Claude).

**Human review:** 0 of 4 decisions right on four blind cases, in 7 minutes, before learning what this data looks
like.

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

Neither the format nor the randomness explains the gap. What's left is the model and two things we haven't
checked: does Claude's 88% hold up on a re-run? And does the phrasing of the instruction (which was drafted with
Claude's assistance) work better with Claude?

## Checking the cause: three prompt changes (Mistral)

Each change was one or two sentences added to the instruction, written with a prediction prior to the run, on all
32 cases (a close-only rerun would not have been able to tell the difference between a model that reads the data
correctly and one that now just closes everything). The bar for "it works" as set prior to the final run: close
goes up, escalate stays near 100% and evidence goes up.

| added to the instruction | Small: close | Small: escalate (single / hub) | Large 3: close | Large 3: escalate | evidence |
|---|---|---|---|---|---|
| nothing (the table above) | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 P04 only |
| "simulated bank… regular payments of the same amount to the same accounts are normal" | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 0% (lost P04) |
| "your objective is to close false alarms… and to escalate real cases" | 6% | 90% / 67% | 0% | 100% / 100% | unchanged |
| both sentences | **69%** | **40% / 33%** | 0% | 100% / 100% | unchanged |

Our predictions were wrong twice ("close around 90%, escalate around 80%"); the third one ("as bad as the last run")
was the one that held for Large 3. No change met the bar at all, the evidence score never went up.

## Where the Mistral models fail

They read **regularity as laundering**. On P17, a normal account, Mistral Large 3 wrote: "multiple repeated
transactions with identical amounts to the same counterparties… suggest potential layering activity", and cited 42
of the 59 rows (Small cited 30). In this simulated bank, a normal customer would make the same payment every day.
Structuring (i.e., splitting the money into a number of payments to stay below the reporting threshold) is a genuine
red flag in the real world, not in this simulation. We made the same mistake in our own blind cases. Large 4, with full
reasoning, flagged 15 of the 16 normal accounts as "structuring" or "smurfing" and cited 38 rows on a typical one. It
also pulls in a real fact from the wrong place: on P11, it says cheques of 55,852.15 SAR are "just below the 60,000
SAR reporting threshold". The 60k SAR is the amount a traveler must declare in cash when crossing into Saudi Arabia
at the border. That is irrelevant here, and the case mentions no threshold at all.

Told that regularity is normal, they stick to it: Small, on P31 with the sentence in the prompt, called the same
repetition "unusual for regular customer behavior". With both sentences, Small turned it around and closed the
laundering accounts with "regular payments… suggest normal customer behavior", escalating on the very large amounts
instead. The feature changed, the method didn't.

On the evidence, they point to the busy, regular rows and overlook the two or three quiet laundering rows: Large 3
passed one case (P04, two foreign-currency payments after self-transfers), in three of the four runs.

## What Claude did differently

It refers to the regular payments as "routine recurring payments" and escalates on the one-off items within them: a
burst of credits from new counterparties (P06, P08), a self-conversion followed by a payout in a different currency
(P03, P04, P10, P13), three payments in the space of a few minutes in three different formats (P09, P12). It misses
the two cycles with only two quiet rows each (P01, P02) and the three hub accounts (P11, P14, P16) whose two-way
flows it treats as "related-entity treasury transfers". It incorrectly escalates P28 ("just under a 10k threshold"
again, the real-world habit) and P32 (a one-off cheque from a new counterparty followed by three fast payments). The
evidence is still very weak in that it often gets the right area but only cites less than half of the laundering
rows.

Read side by side ([`REASONING.md`](REASONING.md), all 32 pairs) the difference is in the method. Claude starts off
by stating what the account normally does, then moves on to the bits that are at all unusual and checks whether
money actually passes through. That is the method that analysts are told to follow: the examiner looks at whether
the activity is typical for the customer
([FFIEC](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04_ep)) and a single red
flag proves nothing on its own
([FATF](https://www.fatf-gafi.org/content/dam/fatf-gafi/brochures/Handout-Red-Flags-VA-Financial-Non-Financial.pdf)).
Large 4 never defines normal so a single feature (repetition) is sufficient. The rows illustrate the limits of
Claude's method: the rows it cites are mostly correct (98 of 130) but it only picks up 98 of the 250 laundering rows
as the laundering on the hub accounts is simply the steady two-way flow that it takes as the normal. Large 4 cites
1,182 rows of which 119 are correct.

## Giving Large 4 Claude's method

We ran Large 4 twice more, on the same 32 cases. These runs look for where the gap comes from; they are not a new
score.

- **A. The method run.** We added Claude's method to the instruction, in three steps: describe what the account
  normally does, list the transactions that depart from it, and check whether money comes in and leaves again soon
  (`variants/method.txt`).
- **C. The neutral-alert run.** The same, but the line "Alert: This account has been flagged for suspicious
  activity." was replaced by "This account was selected for review."

We had planned a third run, B, giving Large 4 a summary of the account computed by code (one line per counterparty),
in case it could not read a long table. We dropped it after run A, as it showed that Large 4 did find the account's
routine and the transactions that departed from it.

| | Large 4 | A: + method | C: + method, neutral alert | Claude |
|---|---|---|---|---|
| normal accounts closed (of 16) | 0 | 1 | 1 | 14 |
| laundering accounts caught (of 16) | 16 | 16 | 16 | 11 |
| rows cited: laundering / other | 119 / 1,063 | 95 / 309 | 133 / 206 | 98 / 32 |

The method took: "structuring" fell from 15 normal accounts to 3, and the rows from 1,182 to 404. The decision did
not move. Large 4's reasoning, saved for these runs, considered closing on 11 of the 16 normal accounts and turned
back on the alert on 10: "But given the alert, we flag the large outgoing transactions as suspicious". With the
alert gone, it leaned on the instruction instead, on 13 of 16: "But the prompt asks for suspicious rows. All are
part of the scheme." Remove one cue that something is there to find, and it leans on the next. The same thing
happened in [The Data Can't Tell](https://github.com/BassmaSH/the-data-cant-tell), where "why did X drop?" made
models find a drop. Claude got the same alert and instruction and was not moved. For training, this points at the
weight the model gives to what a request presupposes, not at its reading of the data. Details in
[`REASONING.md`](REASONING.md).

## What next, and what it costs

1. **Check that Claude's result holds:** run the same 32 cases 3-5 times to see how stable its decisions are without
   temperature 0; then add in fresh accounts it hasn't seen. The risk is reduced only partially by using new
   accounts from another of IBM's datasets (those are public too); it's only eliminated by using regenerated or real
   data.
2. **Better data:** the larger IBM data sets cover a longer period so the monthly rhythm is apparent. A sample of
   anonymised alerts from one bank with the analyst's decisions as the key. That's the only real test of capacity.
3. **For the Mistral models:** five prompt changes on these 32 cases resulted in Large 4's method changing but not
   its decisions. Its reasoning was predicated on whatever in the prompt suggested that there was something to be
   found. The next test is a request that makes absolutely no assumptions (no alert, and an instruction which
   doesn't ask it to "flag the suspicious rows") on new cases rather than these 32. If Large 4 then closes the false
   alarms, the fix belongs in training rather than in the prompt.

## Limits

- **Synthetic data:** no real bank or person involved at all. The simulator has habits that a bank might simply not
  have (daily identical payments, reinvestment transfers to self, very large amounts).
- **Public data:** the IBM dataset has been public since 2023 so any model could have read the descriptions of how
  it behaves.
- **One account, 18 days:** an analyst's best signals (a monthly rhythm, the other accounts in the scheme) are
  completely out of reach. From within one account, a scatter-gather looks precisely the same as a fan-out.
- **32 cases, one run per prompt:** each close case is 6 points on its slice. We tested the three prompt variations
  on the same 32 cases, as well as the method and neutral-alert runs. The Mistral runs are all at temperature 0,
  except one Large 4 check at temperature 1; Claude's single run is not, so its scores could vary on a re-run.
- **Not identical settings:** in the main table, Claude's format was forced by a schema, the Mistral models by JSON
  mode. Claude and Large 4 reason before answering, whereas Small 4 and Large 3 don't. Large 4 was re-run with
  Claude's schema and at temperature 1 (no change). The instruction was drafted with Claude's help (which may work
  better for its runs).
- **Partly hand-picked cases:** half the normal accounts were chosen to look like an alert, which is realistic for an
  alert queue but not a random sample. The rule's thresholds are an example, not a bank's rules.
- **Cost:** around 103,000 prompt tokens per run (around 3,200 per case, the tables of ids and amounts are more
  expensive in terms of tokens). 8 runs of Small 4 and Large 3 at a few cents each. Large 4: 73,355 prompt and
  134,706 completion tokens at around $0.33, two harness reruns at around $0.35 each, the method and neutral-alert
  runs at around $0.40 each. Claude Opus 5.5: 103,549 prompt and 16,455 completion tokens at around $0.74.

## Run it

```bash
python run.py rule                      # the rule baseline, no API call, standard library only
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export MISTRAL_API_KEY=...              # and ANTHROPIC_API_KEY for a Claude model
.venv/bin/python run.py mistral-small-2603
.venv/bin/python run.py mistral-small-2603 both      # a prompt variant from variants/
.venv/bin/python run.py mistral-large-4 schema       # the harness check
.venv/bin/python run.py mistral-large-4 method-neutral   # the method, with a neutral alert
```

Each run produces the per-slice table and stores all the answers in `results/`. `golden.jsonl` contains two lines
per case (the decision and the evidence) which are generated by `make_golden.py` from `cases/` and `keys/`. The
scoring is done by `aml_graders.py`. The runner in `evals_kit/` is a copy of
[evals-kit](https://github.com/BassmaSH/evals-kit).

## The data

IBM's synthetic anti-money-laundering data, split HI-Small (Altman et al., *Realistic Synthetic Financial
Transactions for Anti-Money Laundering Models*, NeurIPS 2023, <https://arxiv.org/abs/2306.16424>), licence
CDLA-Sharing-1.0. Everything is simulated, no real person or real bank. The raw files are not in this repo;
`prep/README.md` has the instructions for rebuilding them and `make_case.py` cuts a case from them. The files that
are derived from that data (`cases/`, `keys/`, `golden.jsonl`) are shared under the same CDLA-Sharing-1.0 licence and
the code is MIT.

## How this was built

I did some quick research on the field, wrote the question, selected cases and slices, set the scoring rule and
prompt, made predictions before each run, and interpreted the results. Claude (Claude Code) wrote the scripts based
on these inputs (including the case builder, graders, rule file, runner script, and model client), reviewed the
models' reasoning in `results/`, maintained records in `NOTEBOOK.md`, and drafted the initial version of this memo
from my notes.
