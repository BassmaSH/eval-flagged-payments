# Can a language model reduce the number of false positives in AML alert queues?

*This is a summary of a very small benchmark we ran over a weekend: 32 flagged accounts from IBM's synthetic bank, a
rule baseline, three Mistral models, and Claude Opus 5.5 as an external reference. The full record is in
[`NOTEBOOK.md`](docs/NOTEBOOK.md), with each prediction logged prior to running.*

**The decision.** Whether to put a language model in front of the alert queue. It would filter out clear false
alarms and pass the rest to an analyst, along with the transactions that actually mattered.

**The test.** A bank's monitoring system flags accounts, and an analyst decides whether to escalate each one or
close it as a false alarm. We took 32 accounts from IBM's synthetic bank data, 16 laundering and 16 normal, showed
each to the model as flagged, and scored its decision and the transactions it cited.

**The result.** The Mistral models, as tested, did not reduce false positives: all three (Small 4, Large 3, and
Large 4) escalated every account and closed none of the 16 false alarms. For comparison, we tested Claude Opus 5.5
four times on the same cases: each time it closed 14 of 16 false alarms and caught 11 or 12 of 16 laundering
accounts. This shows the task can be performed from a single account, and that the gap lies with the models.

**The caveat.** Claude did not come to this test cold. Asked what laundering looks like in a network of
transactions, it lists seven of the eight patterns this data is built from, by name. Those eight come from the
literature the data belongs to (Altman et al., 2023, Figure 2, after Suzumura and Kanezashi's AMLSim), which we read
before building the cases. So this shows it knows that literature, not that it has seen these accounts; we cannot
rule that out either. The data is synthetic, and 32 cases can show a large gap, not a
small one. More testing on more realistic data is required before we can come to any firm conclusions.

## What we understood about the Mistral models

Five readings of how the models work, drawn from the runs below. They are interpretations, not measurements: each
says what it rests on, how sure we are, and what would test it.

| | what the model does | what we saw | how sure | what would test it |
|---|---|---|---|---|
| **1** | **It treats what a request presupposes as evidence.** | Large 4's saved reasoning considered closing 11 of the 16 normal accounts and turned back on 10 because the account was flagged. With "flagged" removed, it cited the instruction to find suspicious rows on 13 of 16. The same effect in [a second experiment](https://github.com/BassmaSH/the-data-cant-tell), where "why did X drop?" made models find a drop. | Medium to high. Another reading fits: it would escalate anyway, and the cue is a justification written afterwards. | A request with no cue at all, on new cases: no alert, and an instruction that does not ask it to flag rows. |
| **2** | **A prompt changes which feature it decides from, not the habit of deciding from one feature.** | Told that regular payments are normal, Small 4 called the same repetition "unusual for regular customer behavior". Told the goal is to close false alarms, it closed 11 normal accounts and 10 laundering ones, and escalated on very large amounts instead. | Medium: seen on Small 4; Large 3 did not move at all. | The same prompt changes on Large 4. |
| **3** | **It applies what is generally true of laundering, without first working out what is normal for this account.** | Large 4 calls routine payments "structuring" on 28 of 32 accounts, and on P11 cites a real Saudi cash-declaration threshold that the case never mentions. Asked to describe the account's normal first, "structuring" falls to 2 of 32. We made the same mistake on four blind cases (0 of 4). | Medium to high: it can do the step when told, and does not do it unprompted. | Cases where a textbook red flag is present and benign, without the method. |
| **4** | **Its analysis does not decide its answer.** | Given Claude's method, Large 4 describes the same routine and picks the same one-off row as Claude (P27), and cites a third of the rows it cited before. It still escalates 15 of the 16 normal accounts. | Medium: two runs. What a model writes while reasoning is not proof of what drove its answer ([Anthropic, 2025](https://www.anthropic.com/research/reasoning-models-dont-say-think)). | The decision with reasoning set low, against the default. |
| **5** | **It has one frame for laundering, the cash framework, and keeps it whatever it is asked.** | On the cases, no Mistral run names a network pattern (fan-out, cycle…) in 13 runs; they say "structuring" and "layering". Asked directly about transaction networks, Large 4 names 3 of the 8 patterns and the others 1; they describe the shapes in other words and still organise the answer by the stages of laundering cash. Claude gives the same cash answer to the general question, and switches to the network patterns (7 of 8) when asked about networks. | Medium: the direct question was asked once, in one wording. | Ask Large 4 to analyse the account as a network of counterparties, without the method, and see whether its decisions move. |

Taken together: a model that decides from the request and from one salient feature, seen through a framework that
does not fit this data. Its analysis can be correct and still not change the decision.

## 1. What is measured, and what is not

32 flagged accounts from IBM's synthetic bank (Sep 1–18, 2022): 16 laundering, 16 normal (8 drawn at random, 8 chosen from 15 candidates because they look most like an alert). The model sees the transactions on one account and a generic alert and then responds in JSON
format with a reason, an ESCALATE or a CLOSE and the IDs of the suspicious rows. Two scores per account: the
**decision** and the **evidence** (for a laundering account more than half of the laundering rows cited and no
normal row; for a normal account no row is cited).

It measures the first step of an analyst's work: one account, one decision, the rows that justify it. It does not
measure following money across accounts, working an alert over weeks, or performance on a real bank's data.

**The data.** IBM's synthetic anti-money-laundering data, split HI-Small (Altman et al., *Realistic Synthetic Financial
Transactions for Anti-Money Laundering Models*, NeurIPS 2023, <https://arxiv.org/abs/2306.16424>), licence
CDLA-Sharing-1.0. Everything is simulated, no real person or real bank. The raw files are not in this repo;
`prep/README.md` has the instructions for rebuilding them and `prep/make_case.py` cuts a case from them. The files that
are derived from that data (everything in `benchmark/`) are shared under the same CDLA-Sharing-1.0 licence and
the code is MIT.

## 2. Result

Runs of 8th November 2026, same prompt for each model; answers in `results/`.

| slice | n | rule (no model) | `mistral-small-2603` | `mistral-large-2512` | `mistral-large-4` | `claude-opus-5-5` |
|---|---|---|---|---|---|---|
| decision: escalate, single scheme | 10 | 30% | 100% | 100% | 100% | 80% |
| decision: escalate, hub account | 6 | 17% | 100% | 100% | 100% | 50% |
| **decision: close (the time saved)** | 16 | **94%** | **0%** | **0%** | **0%** | **88%** |
| evidence: escalate, single scheme | 10 | 10% | 0% | 10% | 0% | 20% |
| evidence: escalate, hub account | 6 | 0% | 0% | 0% | 0% | 17% |
| evidence: close | 16 | 94% | 0% | 0% | 0% | 88% |

Settings: the Mistral models at temperature 0 in JSON mode. Claude takes no temperature setting, can reason
before answering and decides for each request whether to (effort left at its default), and its format was forced
with a schema; it ran four times (Nov 8, and three reruns on Nov 15: the table shows the first). Large 4 also reasons before
answering (about 4,200 output tokens per case, against about 500 for Claude).

**Human review:** 0 of 4 decisions right on four blind cases, in 7 minutes, before learning what this data looks
like.

The rule escalates an account that paid 8 or more different accounts within 3 days. A model that always says
ESCALATE scores 100% on the escalate slices and 0% on close: the three Mistral models scored exactly that. The rule
fails the other way: it closes almost everything, laundering included, so it is a floor.

**How sure are these scores?** With 16 normal accounts, each score has a wide range (exact 95% intervals,
`python report.py`):

| decision | rule | Small | Large 3 | Large 4 | Claude |
|---|---|---|---|---|---|
| close, of 16 | 15 · 70–100% | 0 · 0–21% | 0 · 0–21% | 0 · 0–21% | 14 · 62–98% |
| escalate, single scheme, of 10 | 3 · 7–65% | 10 · 69–100% | 10 · 69–100% | 10 · 69–100% | 8 · 44–97% |
| escalate, hub account, of 6 | 1 · 0–64% | 6 · 54–100% | 6 · 54–100% | 6 · 54–100% | 3 · 12–88% |

On closing, the ranges of Claude and the Mistral models do not overlap. Case by case, on the same 16 normal
accounts, Claude closed 14 that Large 4 escalated and Large 4 closed none that Claude escalated (exact McNemar
test, p = 0.0001). On catching laundering the ranges overlap: Large 4 caught 5 accounts that Claude missed and
Claude none that Large 4 missed (p = 0.06), which 16 cases cannot settle. The solid result is the gap on closing.

## 3. Is it the harness?

Claude's run did not have exactly the Mistral setup: its format was forced by a schema, it ran with normal
randomness, and it can reason before answering. Large 4 already reasons by default, so it was rerun with Claude's
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

## 4. What each model does

### The Mistral models

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

### Claude

It refers to the regular payments as "routine recurring payments" and escalates on the one-off items within them: a
burst of credits from new counterparties (P06, P08), a self-conversion followed by a payout in a different currency
(P03, P04, P10, P13), three payments in the space of a few minutes in three different formats (P09, P12). Across
four runs, it misses the three hub accounts (P11, P14, P16) every time, treating their two-way flows as
"related-entity treasury transfers", and incorrectly escalates P32 every time (a one-off cheque from a new
counterparty followed by three fast payments). Six cases change from one run to the next: the two cycles with only
two quiet rows each (P01, P02), P03, P04, and the normal accounts P17 and P28 ("just under a 10k threshold" again,
the real-world habit). The
evidence is still very weak in that it often gets the right area but only cites less than half of the laundering
rows.

Read side by side ([`REASONING.md`](docs/REASONING.md), all 32 pairs) the difference is in the method. Claude starts off
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

### One normal account, every run (P27)

58 rows: recurring payments to the same few accounts, a cheque of 82,569.50 received ten times from one sender,
and one cheque of 15.7 million received once from a new sender (T017).

| run | the routine | the one-off row | decision |
|---|---|---|---|
| Small, Large 3 | "structuring", "layering"; 11 and 25 rows cited | among the rows cited | ESCALATE |
| Large 4 | the same; 11 rows cited | among the rows cited | ESCALATE |
| Large 4 + method | the account's normal | cited T017, and only T017 | ESCALATE |
| Large 4 + method, neutral alert | the account's normal | cited T017, and only T017 | ESCALATE |
| Claude, four runs | "routine recurring business" | named T017 each time | CLOSE, no row, four times |

With the method, Large 4 finds the same normal and the same one-off row as Claude, and escalates on it: "roughly
190 times larger than the typical inflow". Different from normal is treated as suspicious. Claude checks one more
thing each time, whether the money moved on: "not followed by any rapid onward movement, layering, or structuring",
and closes.

The same check explains the case where Claude is not stable. On P17, the one-off rows are two payments *out* to a new
counterparty (T001, T002). Claude closed it on Nov 8 and escalated it in the three reruns, citing those two rows,
as Large 4 does with the method. Where money left, Claude hesitates; where it only arrived, it closes every time.

### The words each model uses

The number of accounts, out of 32, whose reason contains the term:

| run | fan-out | fan-in | pass-through | layering | structuring | recurring |
|---|---|---|---|---|---|---|
| Small | 0 | 0 | 0 | 24 | 29 | 0 |
| Large 3 | 0 | 0 | 0 | 20 | 21 | 0 |
| Large 4 | 0 | 0 | 2 | 29 | 28 | 1 |
| Large 4 + method | 0 | 0 | 20 | 18 | 2 | 14 |
| Large 4 + method, neutral alert | 0 | 0 | 22 | 18 | 5 | 13 |
| Claude | 16 | 12 | 16 | 22 | 11 | 25 |

The Mistral models describe every account with the vocabulary of cash laundering (structuring, layering), which is
about amounts. Claude also uses the vocabulary of networks (fan-in, fan-out, pass-through), which is about who pays
whom, and it often uses it to rule laundering out: "nothing shows layering, fan-in/fan-out or rapid pass-through".
No Mistral run uses "fan-in" or "fan-out" once, in the answers or in the reasoning saved for the two method runs. With the method,
"structuring" fell from 28 accounts to 2, without being told to. "Pass-through" rose from 2 to 20, but the method's
own text says "check whether money passes through the account", so that word came from the instruction. These
terms are common outside this dataset, so the table says nothing about whether a model has seen the data.

### Asked directly

Two questions with no account and no alert, neither naming a pattern (`python probe.py`, Nov 15, one call each):
"What are the common patterns of money laundering?" and "What patterns of money laundering can be seen in a network
of transactions between bank accounts?" The eight patterns are the ones this data plants. They were introduced in the AMLSim
generator (Suzumura and Kanezashi) and are Figure 2 of the dataset's paper; fan-in, fan-out and cycle are also
general terms for transaction networks.

| model | general question | network question |
|---|---|---|
| Small 4 | the cash stages; 0 of 8 patterns | 1 of 8 (circular flows); "star-like subgraphs", "long chains" |
| Large 3 | the cash stages; 0 of 8 | 1 of 8 (circular flows); "chain structures", "hub-and-spoke", "mesh" |
| Large 4 | the cash stages; 0 of 8 | 3 of 8 (fan-in, fan-out, cycles); "funnel accounts" |
| Claude | the cash stages; 0 of 8 | 7 of 8, as a numbered list of structural patterns |

The Mistral models know the shapes and mostly not the names, and on the network question their headings are still
Structuring, Layering, Integration. Large 4 names fan-in and fan-out here and never used either word in 160 answers
on the cases.

## 5. Testing the cause

### Three prompt changes (Small and Large 3)

Each change was one or two sentences added to the instruction, written with a prediction prior to the run, on all
32 cases (a close-only rerun would not have been able to tell the difference between a model that reads the data
correctly and one that now just closes everything). The bar for "it works" as set prior to the final run: close
goes up, escalate stays near 100% and evidence goes up.

| added to the instruction | Small: close | Small: escalate (single / hub) | Large 3: close | Large 3: escalate | evidence |
|---|---|---|---|---|---|
| nothing (the table above) | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 P04 only |
| "simulated bank… regular payments of the same amount to the same accounts are normal" | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 0% (lost P04) |
| "your objective is to close false alarms… and to escalate real cases" | 6% | 90% / 67% | 0% | 100% / 100% | unchanged |
| both sentences | **69%** | **40% / 33%** | 0% | 100% / 100% | unchanged on laundering accounts; Small 69% on normal accounts, since an account closed with no row cited passes |

Our predictions were wrong twice ("close around 90%, escalate around 80%"); the third one ("as bad as the last run")
was the one that held for Large 3. No change met the bar at all, the evidence score never went up.

### Giving Large 4 Claude's method

We ran Large 4 twice more, on the same 32 cases. These runs look for where the gap comes from; they are not a new
score.

- **A. The method run.** We added Claude's method to the instruction, in three steps: describe what the account
  normally does, list the transactions that depart from it, and check whether money comes in and leaves again soon
  (`src/variants/method.txt`).
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
not move. The evidence did: on single-scheme laundering accounts, Large 4 passed the evidence rule on 3 of 10 with
the method and 2 of 10 with the neutral alert, against 0 of 10 without. Large 4's reasoning, saved for these runs, considered closing on 11 of the 16 normal accounts and turned
back on the alert on 10: "But given the alert, we flag the large outgoing transactions as suspicious". With the
alert gone, it leaned on the instruction instead, on 13 of 16: "But the prompt asks for suspicious rows. All are
part of the scheme." Remove one cue that something is there to find, and it leans on the next. The same thing
happened in [The Data Can't Tell](https://github.com/BassmaSH/the-data-cant-tell), where "why did X drop?" made
models find a drop. Claude got the same alert and instruction and was not moved. For training, this points at the
weight the model gives to what a request presupposes, not at its reading of the data. Details in
[`REASONING.md`](docs/REASONING.md).

## 6. Limits

- **Synthetic data:** no real bank or person involved at all. The simulator has habits that a bank might simply not
  have (daily identical payments, reinvestment transfers to self, very large amounts).
- **Public data:** the IBM dataset has been public since 2023 so any model could have read the descriptions of how
  it behaves.
- **One account, 18 days:** an analyst's best signals (a monthly rhythm, the other accounts in the scheme) are
  completely out of reach. From within one account, a scatter-gather looks precisely the same as a fan-out.
- **32 cases, one run per prompt:** each close case is 6 points on its slice. We tested the three prompt variations
  on the same 32 cases, as well as the method and neutral-alert runs. The Mistral runs are all at temperature 0,
  except one Large 4 check at temperature 1; Claude's runs are not: over four runs its totals held and six cases
  changed.
- **Not identical settings:** in the main table, Claude's format was forced by a schema, the Mistral models by JSON
  mode. Large 4 reasons before answering and Claude can (it decides per request), whereas Small 4 and Large 3 don't. Large 4 was re-run with
  Claude's schema and at temperature 1 (no change). The instruction was drafted with Claude's help (which may work
  better for its runs).
- **Partly hand-picked cases:** half the normal accounts were chosen to look like an alert, which is realistic for an
  alert queue but not a random sample. The rule's thresholds are an example, not a bank's rules.
- **Cost:** around 103,000 prompt tokens per run (around 3,200 per case, the tables of ids and amounts are more
  expensive in terms of tokens). 8 runs of Small 4 and Large 3 at a few cents each. Large 4: 73,355 prompt and
  134,706 completion tokens at around $0.33, two harness reruns at around $0.35 each, the method and neutral-alert
  runs at around $0.40 each. Claude Opus 5.5: 103,549 prompt and 16,455 completion tokens at around $0.74.

- **The rule's thresholds:** "8 accounts in 3 days" is one example of a rule that detects a single pattern, fan-out,
  by counting. It was fixed before the runs. Scored afterwards at 4, 6, 8, 10 and 12 accounts over 1, 3 and 7 days,
  it catches between 0% and 50% of the single-scheme laundering accounts. The published setting is not the best one:
  6 accounts in 1 day catches 40% (against 30%) and closes the same 94% of normal accounts. No setting catches more
  than half, so the comparison with the models does not depend on the thresholds chosen.

- **Output tokens:** Claude used about 12% of Large 4's output tokens (about 500 per case against 4,200). The
  reasoning effort was left at each API's default and not matched: Claude decides for each request whether to reason
  at all, and Large 4's saved reasoning rewrites the whole table before deciding. This is not a like-for-like
  measure of efficiency.

## 7. What next, and what it costs

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

4. **Knowledge or judgement?** The method gave Large 4 a procedure, not the laundering patterns, and it never
   names one in any run. Giving it the pattern definitions without the method, on the same cases, would show
   whether the gap is in what it knows or in how it decides.

## 8. Timeline

Each run's prediction is in [`docs/NOTEBOOK.md`](docs/NOTEBOOK.md), in the author's words.

| date | step | prediction, and whether it held |
|---|---|---|
| Nov 7 | data rebuilt from IBM's files, cases cut | |
| Nov 8 | four blind cases worked by hand: 0 of 4 decisions right | answers written before opening the keys |
| Nov 8 | rule, Small 4, Large 3 | written while the first run was in progress: "close lower than the rule" held, "evidence above 50%" did not |
| Nov 8 | three prompt changes, on Small 4 and Large 3 | "close around 90%", twice: did not hold. "As bad as the last run": held for Large 3 |
| Nov 8 | Large 4 | "almost as bad": held |
| Nov 8 | Claude Opus 5.5, as an outside reference | "same results": did not hold |
| Nov 9 | Large 4 with Claude's schema | "same perf": held |
| Nov 9 | the same at temperature 1 | no prediction written |
| Nov 11 | Large 4 with the method | "will do better but less good than Claude": 1 normal account closed, from 0 |
| Nov 11–12 | the same with a neutral alert | "does better than the last run": did not hold on the decision |
| Nov 15 | second reading of the saved answers; tests, `report.py`, ranges | no model called |

## 9. Reproduce it

```bash
python report.py                        # the tables above, rebuilt from results/, no API call
pytest -q                               # 48 checks, no API call (pip install pytest)
python run.py rule                      # the rule baseline, no API call, standard library only
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export MISTRAL_API_KEY=...              # and ANTHROPIC_API_KEY for a Claude model
# Saved answers are never replaced: a rerun needs a name of its own (repeat2, repeat3, ...).
# A run that stops is resumed by the same command: answers are written as they arrive.
.venv/bin/python run.py mistral-small-2603 repeat2
.venv/bin/python run.py mistral-small-2603 both repeat2      # a prompt variant (the VARIANTS table in run.py)
.venv/bin/python run.py mistral-large-4 schema repeat2       # the harness check
.venv/bin/python run.py mistral-large-4 method-neutral repeat2   # the method, with a neutral alert
```

Each run produces the per-slice table and stores all the answers in `results/`. Since Nov 15, 2026, a model run
also stores `<name>.meta.json` (the settings, the prompt as sent, the date, the library versions and the tokens per
case); the runs reported above were made before that. `benchmark/golden.jsonl` contains two lines
per case (the decision and the evidence) which are generated by `prep/make_golden.py` from `benchmark/cases/` and
`benchmark/keys/`. The scoring is done by `src/aml_graders.py`. The runner in `src/evals_kit/` is a copy of
[evals-kit](https://github.com/BassmaSH/evals-kit).

**Where things are.**

| path | what it holds |
|---|---|
| `run.py` | runs one system on the 32 cases and saves its answers |
| `report.py` | rebuilds every table above from `results/` |
| `probe.py` | asks a model about laundering patterns directly, with no account |
| `benchmark/` | the test: `golden.jsonl` (the expected answers), `cases/` (what the model sees), `keys/` (the answer keys) |
| `src/` | what the two commands are made of: |
| `src/system.py`, `src/variants/` | the model under test, the prompt, and the paragraphs added to it |
| `src/rule.py` | the baseline with no model |
| `src/aml_graders.py` | the two scoring rules |
| `src/stats.py` | the ranges and the paired test |
| `src/evals_kit/` | the runner, a copy of evals-kit |
| `results/` | every saved answer, and the saved reasoning of the two method runs |
| `prep/` | rebuilds the data and the cases |
| `tests/` | 48 checks on the scoring, the command line, the statistics, resuming a run and the term lists, no API call |
| `docs/` | the notebook, and the two models' reasoning side by side |

**Is the scoring itself right?** 21 tests on the scoring (`tests/test_aml_graders.py`), 9 on the command line and 7
on the statistics; `report.py`, which grades every
saved answer again and rebuilds the tables above; a settings file saved with each new run; and `run.py` no longer
replaces saved answers. Grading the 960 saved answers again gave the same verdict for each.
Conventions for changing the code are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

### How this was built

I did some quick research on the field, wrote the question, selected cases and slices, set the scoring rule and
prompt, made predictions before each run, and interpreted the results. Claude (Claude Code) wrote the scripts based
on these inputs (including the case builder, graders, rule file, runner script, and model client), reviewed the
models' reasoning in `results/`, maintained records in `docs/NOTEBOOK.md`, and drafted the initial version of this memo
from my notes.
