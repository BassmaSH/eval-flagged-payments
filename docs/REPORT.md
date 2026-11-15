# The full report

*The detailed evidence behind the [README](../README.md): the checks on the setup, what each model does, the tests of
the cause, the limits, what to do next and the timeline. Every table is rebuilt by `python report.py`. The record
of the work as it happened, with each prediction, is in [`NOTEBOOK.md`](NOTEBOOK.md).*

## 1. Is it the harness?

Claude's run did not have exactly the Mistral setup: its format was forced by a schema, it ran with normal
randomness, and it can reason before answering. Large 4 already reasons by default, so it was rerun with Claude's
schema (one change), then the same at temperature 1 (one more change). Prediction for the first: "same perf this
run with temp 0".

| Large 4 run | close | escalate (single / hub) | evidence (single / hub) | output tokens |
|---|---|---|---|---|
| JSON mode, temperature 0 | 0% | 100% / 100% | 0% / 0% | 134,706 |
| Claude's schema, temperature 0 | 0% | 100% / 100% | 0% / 0% | 142,781 |
| Claude's schema, temperature 1 | 0% | 100% / 100% | 10% / 0% | 138,796 |

Neither the format nor the randomness explains the gap, and Claude's 88% held on three reruns. One thing is still
unchecked: whether the phrasing of the instruction, which was drafted with Claude's assistance, works better with
Claude.

## 2. What each model does

### The Mistral models

They read **regularity as laundering**. On P17, a normal account, Mistral Large 3 wrote: "multiple repeated
transactions with identical amounts to the same counterparties… suggest potential layering activity", and cited 42
of the 59 rows (Small cited 30). In this simulated bank, a normal customer would make the same payment every day.
Structuring (i.e., splitting the money into a number of payments to stay below the reporting threshold) is a genuine
red flag in the real world, not in this simulation. We made the same mistake in our own blind cases. Large 4, with
full reasoning, flagged 15 of the 16 normal accounts as "structuring" or "smurfing" and cited 38 rows on a typical
one. It also pulls in a real fact from the wrong place: on P11, it says cheques of 55,852.15 SAR are "just below the
60,000 SAR reporting threshold". The 60k SAR is the amount a traveler must declare in cash when crossing into Saudi
Arabia at the border. That is irrelevant here, and the case mentions no threshold at all.

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
the real-world habit). The evidence is still very weak in that it often gets the right area but only cites less
than half of the laundering rows.

Read side by side ([`REASONING.md`](REASONING.md), all 32 pairs) the difference is in the method. Claude starts
off by stating what the account normally does, then moves on to the bits that are at all unusual and checks whether
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

P17 is the opposite case. There the one-off rows are two payments *out* to a new counterparty (T001, T002). Claude
closed it on Nov 8 and escalated it in the three reruns, citing those two rows, as Large 4 does with the method.

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
Where it asserts a pattern on a single-scheme account, it matches the answer key (P03, P06, P08, P10). "Pass-through"
in the method runs came from the instruction, whose text says "check whether money passes through the account".

### Asked directly

Two questions with no account and no alert, neither naming a pattern (`python probe.py`, Nov 15, one call each):
"What are the common patterns of money laundering?" and "What patterns of money laundering can be seen in a network
of transactions between bank accounts?" The eight patterns are the ones this data plants. They were introduced in
the AMLSim generator (Suzumura and Kanezashi) and are Figure 2 of the dataset's paper; fan-in, fan-out and cycle
are also general terms for transaction networks.

| model | general question | network question |
|---|---|---|
| Small 4 | the cash stages; 0 of 8 patterns | 1 of 8 (circular flows); "star-like subgraphs", "long chains" |
| Large 3 | the cash stages; 0 of 8 | 1 of 8 (circular flows); "chain structures", "hub-and-spoke", "mesh" |
| Large 4 | the cash stages; 0 of 8 | 3 of 8 (fan-in, fan-out, cycles); "funnel accounts" |
| Claude | the cash stages; 0 of 8 | 7 of 8, as a numbered list of structural patterns |

The Mistral models know the shapes and mostly not the names, and on the network question their headings are still
Structuring, Layering, Integration. Large 4 names fan-in and fan-out here and never used either word in 160 answers
on the cases.

## 3. Testing the cause

### Three prompt changes (Small and Large 3)

Each change was one or two sentences added to the instruction, written with a prediction prior to the run, on all
32 cases (a close-only rerun would not have been able to tell the difference between a model that reads the data
correctly and one that now just closes everything). The bar for "it works" as set prior to the final run: close
goes up, escalate stays near 100% and evidence goes up.

| added to the instruction | Small: close | Small: escalate (single / hub) | Large 3: close | Large 3: escalate | evidence |
|---|---|---|---|---|---|
| nothing (the main table in the README) | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 P04 only |
| "simulated bank… regular payments of the same amount to the same accounts are normal" | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 0% (lost P04) |
| "your objective is to close false alarms… and to escalate real cases" | 6% | 90% / 67% | 0% | 100% / 100% | unchanged |
| both sentences | **69%** | **40% / 33%** | 0% | 100% / 100% | unchanged on laundering accounts; Small 69% on normal accounts, since an account closed with no row cited passes |

Our predictions were wrong twice ("close around 90%, escalate around 80%"); the third one ("as bad as the last run")
was the one that held for Large 3. No change met the bar at all, the evidence score never went up.

Told that regularity is normal, they stick to it: Small, on P31 with the sentence in the prompt, called the same
repetition "unusual for regular customer behavior". With both sentences, Small turned it around and closed the
laundering accounts with "regular payments… suggest normal customer behavior", escalating on the very large amounts
instead. The feature changed, the method didn't.

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
| evidence passed, single scheme (of 10) | 0 | 3 | 2 | 2 |

The method took: "structuring" fell from 28 of the 32 accounts to 2, and the rows from 1,182 to 404. The decision
did not move. Large 4's reasoning, saved for these runs, considered closing on 11 of the 16 normal accounts and
turned back on the alert on 10: "But given the alert, we flag the large outgoing transactions as suspicious". With
the alert gone, it leaned on the instruction instead, on 13 of 16: "But the prompt asks for suspicious rows. All are
part of the scheme." Remove one cue that something is there to find, and it leans on the next. Claude got the same
alert and instruction and was not moved. Details in [`REASONING.md`](REASONING.md).

## 4. Limits

- **Synthetic data:** no real bank or person involved at all. The simulator has habits that a bank might simply not
  have (daily identical payments, reinvestment transfers to self, very large amounts).
- **Public data:** the IBM dataset has been public since 2023 so any model could have read the descriptions of how
  it behaves.
- **One account, 18 days:** an analyst's best signals (a monthly rhythm, the other accounts in the scheme) are
  completely out of reach. From within one account, a scatter-gather looks precisely the same as a fan-out.
- **32 cases, one run per prompt for the Mistral models:** each close case is 6 points on its slice. We tested the
  three prompt variations on the same 32 cases, as well as the method and neutral-alert runs. The Mistral runs are
  all at temperature 0, except one Large 4 check at temperature 1; Claude's runs are not: over four runs its totals
  held and six cases changed.
- **Not identical settings:** Claude's format was forced by a schema, the Mistral models by JSON mode, and the
  reasoning effort was left at each API's default. The instruction was drafted with Claude's help (which may work
  better for its runs).
- **Partly hand-picked cases:** half the normal accounts were chosen to look like an alert, which is realistic for an
  alert queue but not a random sample.
- **The rule's thresholds:** "8 accounts in 3 days" is an example, not a bank's rule, fixed before the runs. Scored
  afterwards at 4 to 12 accounts over 1 to 7 days, it catches between 0% and 50% of the single-scheme laundering
  accounts, so the comparison with the models does not depend on the thresholds chosen.
- **Output tokens are not a like-for-like measure:** Large 4 uses about 4,200 per case, much of it rewriting the
  table; Claude about 510, of which about 350 are reasoning, on 29 or 30 of the 32 cases (measured on the reruns).
  The effort settings were not matched.
- **Cost:** around 103,000 prompt tokens per run (around 3,200 per case, the tables of ids and amounts are more
  expensive in terms of tokens). 8 runs of Small 4 and Large 3 at a few cents each. Large 4: 73,355 prompt and
  134,706 completion tokens at around $0.33, two harness reruns at around $0.35 each, the method and neutral-alert
  runs at around $0.40 each. Claude Opus 5.5: 103,549 prompt and about 16,500 completion tokens per run, around
  $0.75, four times.

## 5. What next, and what it costs

Each reading in the [README](../README.md#1-what-we-understood-about-the-mistral-models) names the test that would settle it. Beyond those:

1. **Claude on accounts it has not seen.** Its result held on four runs of the same 32 cases; that measures luck,
   not memory. The risk is reduced only partially by using new accounts from another of IBM's datasets (those are
   public too); it's only eliminated by using regenerated or real data.
2. **Better data:** the larger IBM data sets cover a longer period so the monthly rhythm is apparent. A sample of
   anonymised alerts from one bank with the analyst's decisions as the key. That's the only real test of capacity.
3. **For the Mistral models:** a request that makes absolutely no assumptions (no alert, and an instruction which
   doesn't ask it to "flag the suspicious rows") on new cases rather than these 32. If Large 4 then closes the false
   alarms, the fix belongs in training rather than in the prompt.

## 6. Timeline

Each run's prediction is in [`docs/NOTEBOOK.md`](NOTEBOOK.md), in the author's words.

| date | step | prediction, and whether it held |
|---|---|---|
| **First weekend** | | |
| Nov 7 | data rebuilt from IBM's files, cases cut | |
| Nov 8 | four blind cases worked by hand: 0 of 4 decisions right | answers written before opening the keys |
| Nov 8 | rule, Small 4, Large 3 | written while the first run was in progress: "close lower than the rule" held, "evidence above 50%" did not |
| Nov 8 | three prompt changes, on Small 4 and Large 3 | "close around 90%", twice: did not hold. "As bad as the last run": held for Large 3 |
| Nov 8 | Large 4 | "almost as bad": held |
| Nov 8 | Claude Opus 5.5, as an outside reference | "same results": did not hold |
| **The week after** | | |
| Nov 9 | Large 4 with Claude's schema | "same perf": held |
| Nov 9 | the same at temperature 1 | no prediction written |
| Nov 11 | Large 4 with the method | "will do better but less good than Claude": 1 normal account closed, from 0 |
| Nov 11–12 | the same with a neutral alert | "does better than the last run": did not hold on the decision |
| **Second weekend** | | |
| Nov 15 | the code reviewed: tests, `report.py`, ranges, resumable runs | no model called |
| Nov 15 | Claude, three reruns | "about the same 13-15" normal accounts closed: held (14, 14, 14) |
| Nov 15 | four models asked directly about laundering patterns | Mistral: "question 1 about cash stages" held, "question 2 to list everything" did not. Claude: "patterns in both" held on the network question only |
