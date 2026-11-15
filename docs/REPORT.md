# The full report

*The detailed evidence behind the [README](../README.md): the checks on the setup, what each model does, the tests of
the cause, the limits, what to do next and the timeline. Every table is rebuilt by `python report.py`. The record
of the work as it happened, with each prediction, is in [`NOTEBOOK.md`](NOTEBOOK.md). The questions behind section 2 are the author's: why Claude did better, whether the cited rows were right (which corrected two of Claude's first readings), whether the 60,000 SAR threshold is real, and what to test next.*

## 1. Is it the harness?

Claude's setup differed from the Mistral models': a schema forced its format, it ran with normal randomness, and it can reason before answering. Large 4 already reasons by default, so we reran it with Claude's schema (one change), then at temperature 1 (one more). Prediction for the first: "same perf this
run with temp 0".

| Large 4 run | close | escalate (single / hub) | evidence (single / hub) | output tokens |
|---|---|---|---|---|
| JSON mode, temperature 0 | 0% | 100% / 100% | 0% / 0% | 134,706 |
| Claude's schema, temperature 0 | 0% | 100% / 100% | 0% / 0% | 142,781 |
| Claude's schema, temperature 1 | 0% | 100% / 100% | 10% / 0% | 138,796 |

Neither the format nor the randomness explains the gap, and Claude's 88% held on three reruns. Still unchecked: whether the instruction, drafted with Claude's help, suits Claude better.

## 2. What each model does

These descriptions rest on the one-or-two-sentence `reason` field each model wrote inside its answer. It summarises
the reasoning; it is not the reasoning itself. Large 4's reasoning is saved for the two method runs only (section
3). Claude's is not returned by the API, which reports only how many tokens it spent reasoning. Every answer is in
[`ANSWERS.md`](ANSWERS.md), account by account.

### The Mistral models

They read **regularity as laundering**. On P17, a normal account, Mistral Large 3 wrote: "multiple repeated
transactions with identical amounts to the same counterparties… suggest potential layering activity", and cited 42
of the 59 rows (Small cited 30). In this simulated bank, a normal customer makes the same payment every day.
Structuring (splitting money into several payments to stay below the reporting threshold) is a genuine red flag in the real world, not in this simulation. We made the same mistake in our own blind cases. Large 4, with
full reasoning, flagged 15 of the 16 normal accounts as "structuring" or "smurfing" and cited 38 rows on a typical
one. It also pulls in a real fact from the wrong place: on P11, it says cheques of 55,852.15 SAR are "just below the
60,000 SAR reporting threshold". The 60k SAR is what a traveler must declare in cash at the Saudi border ([ZATCA](https://zatca.gov.sa/en/RulesRegulations/Taxes/Pages/customs_individual/Travel_pages/declare.aspx)), reportedly lowered to SAR 40,000 in 2026 ([Zawya](https://www.zawya.com/en/world/middle-east/saudi-arabia-lowers-mandatory-declaration-threshold-for-cash-valuables-at-borders-gplzlfdk)). It is irrelevant here, and the case mentions no threshold.

On the evidence, they point to the busy, regular rows and overlook the two or three quiet laundering rows: Large 3
passed one case (P04, two foreign-currency payments after self-transfers), in three of the four runs.

### Claude

It refers to the regular payments as "routine recurring payments" and escalates on the one-off items within them: a
burst of credits from new counterparties (P06, P08), a self-conversion followed by a payout in a different currency
(P03, P04, P10, P13), three payments within a few minutes in three different formats (P09, P12). Across
four runs, it misses the three hub accounts (P11, P14, P16) every time, treating their two-way flows as
"related-entity treasury transfers", and incorrectly escalates P32 every time (a one-off cheque from a new
counterparty followed by three fast payments). Six cases change from one run to the next: the two cycles with only
two quiet rows each (P01, P02), P03, P04, and the normal accounts P17 and P28 ("just under a 10k threshold" again,
the real-world habit). The evidence is still weak: it often finds the right area but cites fewer than half of the laundering rows.

Read side by side ([`ANSWERS.md`](ANSWERS.md), all 32 pairs) the difference is in the method. Claude first states what the account normally does, then looks at what is unusual and checks whether money actually passes through. That is the method analysts are told to follow: the examiner looks at whether
the activity is typical for the customer
([FFIEC](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04_ep)) and a single red
flag proves nothing on its own
([FATF](https://www.fatf-gafi.org/content/dam/fatf-gafi/brochures/Handout-Red-Flags-VA-Financial-Non-Financial.pdf)).
Large 4 never defines normal, so a single feature (repetition) is enough, and it uses "structuring" without the part that defines it, amounts kept under a reporting limit. The rows show the limit of Claude's method: those it cites are mostly correct (98 of 130 on Nov 8, and between 69% and 78% over the four runs), but it finds only 98 of the 250 laundering rows, because on the hub accounts the laundering is the steady two-way flow it takes as normal. Large 4 cites
1,182 rows of which 119 are correct.

### Where Claude's method breaks

On Nov 8 Claude made seven wrong decisions: five laundering accounts closed (P01, P02, P11, P14, P16) and two
normal ones escalated (P28, P32). They fall into three kinds, and the three reruns show which are repeatable.

- **Two rows that don't make a pattern (P01, P02, single accounts).** Claude saw the laundering rows and named them,
  then judged them too small to matter. P01's two laundering rows are the Yuan payment and the incoming ACH:
  "The single Yuan ACH payment and one incoming ACH show no layering, structuring or rapid pass-through pattern."
  In this data a laundering attempt often touches only two rows of the flagged account; the rest of the chain sits
  in other accounts, which the model never sees. Not repeatable: over the four runs it closed P01 three times and P02 twice.
- **Laundering that looks like business between related accounts (P11, P14, P16, hub accounts).** On these, the
  laundering is the heavy two-way flow with one or two counterparties: on P14, 23 laundering rows, all with two
  accounts at the same bank. Claude: "two-way ACH churn with two accounts at the same bank… which looks like
  related-entity treasury transfers." It read the same kind of flow as layering on P05 ("irregular, bidirectional
  ACH flows… looks like funds being cycled"), so it is not consistent here. Repeatable: closed in all four runs.
- **A one-off burst on a normal account (P28, P32).** On P32: "A one-off 116,592.50 CHF cheque from a new
  counterparty… followed the same evening by three rapid payments… to another new counterparty… This looks like
  pass-through layering." By Claude's own rule this is the right thing to flag; in this data it was ordinary. P32 is escalated in all four runs; P28 only on Nov 8.

So Claude is better at the decision because it asks the analyst's question, "what is unusual for this account?",
rather than "what here resembles a laundering label?". But the rows show the limit of that question: when the
laundering is a large, steady part of the account, it becomes the "normal" Claude compares against.

One difference from a real analyst: in a bank the baseline comes from the customer file (business type, expected
volumes, what the customer declared when opening the account). These cases have no file, so the account's own
history is the only baseline there is. Claude used it.

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

### Three more pairs

The answers of Nov 8. Claude gave the same decision on these three accounts in all four runs.

**Same feature, opposite reading (P22, normal).**
- Claude, CLOSE: "The account repeats the same fixed set of payments almost every day to the same three
  counterparties, with identical amounts and payment formats. This looks like scheduled recurring obligations…"
- Large 4, ESCALATE, 49 rows: "identical transaction amounts… repeated exactly 7 times each to the same
  counterparties over a 9-day period, indicating potential money laundering to evade reporting thresholds."

**A baseline first, then the departure from it (P07, laundering).**
- Claude, ESCALATE, 2 rows: it describes the routine (daily conversions, a daily cheque, weekly payments), then
  finds the one thing that breaks it: "4,409.63 arrives… and 4,409.56 goes back to that same account about 1.5
  days later, a near-exact pass-through… unlike any other flow with this counterparty." Right decision, but only
  2 of the 49 laundering rows: 47 of the account's 48 transactions with that counterparty (8021353D0) are
  laundering, and Claude treated the other 46 as the normal background it compared against.
- Large 4, ESCALATE, 81 rows: it calls the routine itself laundering ("repeated identical large self-transfers…
  repeated identical large cheque deposits") and cites most of the account, none of them laundering rows (0 of
  49). Right decision for the wrong reason.

**Following the money (P26, normal).**
- Claude, CLOSE: "Inflows (about 13.9k BRL per day) far exceed outflows (about 4.7k), so funds are not being
  passed through." It checks whether money actually moves through the account.
- Large 4, ESCALATE: "identical amounts… repeated exactly across three counterparties over 10 days… indicating
  systematic money laundering activity." No look at whether the money stays or leaves.

**A detail the case does not support (P19, normal).**
- Large 4 on P19 (normal): small card payments "at suspicious hours between 00:05 and 00:28". In this data, many
  ordinary payments carry timestamps just after midnight.

### Did they cite the right rows?

Counted on the runs of Nov 8.

The grader's rule, set before any run: on a laundering account, cite more than half of the laundering rows and no
normal row; on a normal account, cite nothing. The keys are in `benchmark/keys/`. "Right" is a cited row that is a
laundering row; "wrong" is any other cited row.

| | Claude Opus 5.5 | Large 4 |
|---|---|---|
| rows cited, all 32 accounts | 130 | 1,182 |
| of which laundering rows | 98 (75 %) | 119 (10 %) |
| laundering rows found, of 250 | 98 (39 %) | 119 (48 %) |
| rows test passed, 16 laundering accounts | 3 (P03, P05, P15) | 0 |
| rows test passed, 16 normal accounts (cited nothing) | 14 | 0 |

Large 4 finds a few more laundering rows only because it cites nearly everything: about 9 wrong rows for each right
one. Claude's rows are mostly right but too few. Even where Claude escalates, it usually cites the one departure it
noticed and stops (P07: 2 of 49; P09: 3 rows, none of them laundering).

Per account, as cited / right / wrong:

| account | laundering rows | all rows | Claude | rows test | Large 4 | rows test |
|---|---|---|---|---|---|---|
| P01 | 2 | 19 | 0 / 0 / 0 | fail | 15 / 1 / 14 | fail |
| P02 | 2 | 13 | 0 / 0 / 0 | fail | 10 / 2 / 8 | fail |
| P03 | 12 | 27 | 12 / 12 / 0 | pass | 26 / 12 / 14 | fail |
| P04 | 2 | 6 | 4 / 2 / 2 | fail | 5 / 2 / 3 | fail |
| P05 | 34 | 139 | 33 / 33 / 0 | pass | 90 / 0 / 90 | fail |
| P06 | 13 | 155 | 14 / 13 / 1 | fail | 90 / 13 / 77 | fail |
| P07 | 49 | 139 | 2 / 2 / 0 | fail | 81 / 0 / 81 | fail |
| P08 | 27 | 39 | 22 / 20 / 2 | fail | 30 / 20 / 10 | fail |
| P09 | 33 | 56 | 3 / 0 / 3 | fail | 22 / 4 / 18 | fail |
| P10 | 12 | 57 | 24 / 12 / 12 | fail | 57 / 12 / 45 | fail |
| P11 | 10 | 26 | 0 / 0 / 0 | fail | 23 / 10 / 13 | fail |
| P12 | 2 | 28 | 3 / 0 / 3 | fail | 26 / 2 / 24 | fail |
| P13 | 2 | 29 | 3 / 2 / 1 | fail | 26 / 0 / 26 | fail |
| P14 | 23 | 46 | 0 / 0 / 0 | fail | 36 / 14 / 22 | fail |
| P15 | 2 | 47 | 2 / 2 / 0 | pass | 45 / 2 / 43 | fail |
| P16 | 25 | 63 | 0 / 0 / 0 | fail | 62 / 25 / 37 | fail |
| P17–P32 (normal) | 0 | 11–59 | 0 on 14, 4 on P28 and P32 | 14 pass | 5 to 58 each | 0 pass |

Some of Claude's "wrong" rows may be defensible: P04's two extra rows are the self-transfers that fund the two
laundering payouts, and P10's twelve extra rows are the matching self-conversions, one before each payout. The
grader counts them as normal rows.

### The words each model uses

The number of accounts, out of 32, whose reason contains the term:

| run | fan-out | fan-in | pass-through | layering | structuring | recurring |
|---|---|---|---|---|---|---|
| Small | 0 | 0 | 0 | 24 | 29 | 0 |
| Large 3 | 0 | 0 | 0 | 20 | 21 | 0 |
| Large 4 | 0 | 0 | 2 | 29 | 28 | 1 |
| Large 4 + method | 0 | 0 | 20 | 18 | 2 | 14 |
| Large 4 + method, neutral alert | 0 | 0 | 22 | 18 | 5 | 13 |
| Claude (Nov 8) | 16 | 12 | 16 | 22 | 11 | 25 |

The Mistral models describe every account with the vocabulary of cash laundering (structuring, layering), which is
about amounts. Claude also uses the vocabulary of networks (fan-in, fan-out, pass-through), which is about who pays
whom, and it often uses it to rule laundering out: "nothing shows layering, fan-in/fan-out or rapid pass-through".
Where it asserts a pattern on a single-scheme account, it matches the answer key (P03, P06, P08, P10, on Nov 8). "Pass-through"
in the method runs came from the instruction, whose text says "check whether money passes through the account".

By group of accounts, on Nov 8. How many of the 16 reasons use each word, per group of accounts. "Rows" is how many transactions the model
cited as suspicious (the middle value of the 16).

| run | accounts | "structuring" or "smurfing" | "recurring", "routine" or "scheduled" | "classic" | rows cited |
|---|---|---|---|---|---|
| Claude Opus 5.5 | laundering | 1 | 12 | 0 | 3 |
| Claude Opus 5.5 | normal | 11* | 16 | 0 | 0 |
| Large 4 | laundering | 15 | 0 | 8 | 30 |
| Large 4 | normal | 15 | 1 | 11 | 38 |
| Large 4, Claude's schema | normal | 15 | 1 | 9 | 44 |
| Large 4, schema, temperature 1 | normal | 16 | 3 | 4 | 48 |

\* Claude uses the word to rule it out: "no layering, structuring or rapid pass-through".

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
Structuring, Layering, Integration. Large 4 names fan-in and fan-out here and never used either word in 160 answers on the cases.

We then gave Large 4 the four names it had not used and asked it to define each (`python probe.py definitions
mistral-large-4`), with a fifth name we invented, "hinge-loop", as a control.

| asked to define | the shape it describes | correct |
|---|---|---|
| scatter-gather | a large sum split into many small transactions, then recombined | yes |
| gather-scatter | many deposits into one account, then dispersed to many | yes |
| bipartite | funds between two separate groups of accounts | yes |
| stack | deposits under a reporting threshold, "stacked" into a larger balance | no |
| hinge-loop (invented) | funds leaving and returning through a "hinge" account | no such pattern |

It defined the invented pattern too, after noting it "is not one of FATF's standardized typology labels". So its
correct definitions are not proof that it knew those patterns: the first two can be worked out from the words,
and "bipartite" is a general term. "Stack" cannot, and it is the one it got wrong. All five answers come back to
structuring under reporting thresholds; it calls scatter-gather "smurfing or structuring". Large 4 probably does
not know this data's taxonomy as such, and when given it by name, it still reads it as a way of splitting cash.

## 3. Testing the cause

### Three prompt changes (Small and Large 3)

Each change added one or two sentences to the instruction, with a prediction written before the run, on all 32 cases: a close-only rerun could not tell a model that reads the data correctly from one that now closes everything. The bar for "it works", set before the final run: close
goes up, escalate stays near 100% and evidence goes up.

| added to the instruction | Small: close | Small: escalate (single / hub) | Large 3: close | Large 3: escalate | evidence |
|---|---|---|---|---|---|
| nothing (the main table in the README) | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 P04 only |
| "simulated bank… regular payments of the same amount to the same accounts are normal" | 0% | 100% / 100% | 0% | 100% / 100% | Small 0%, Large 3 0% (lost P04) |
| "your objective is to close false alarms… and to escalate real cases" | 6% | 90% / 67% | 0% | 100% / 100% | unchanged |
| both sentences | **69%** | **40% / 33%** | 0% | 100% / 100% | unchanged on laundering accounts; Small 69% on normal accounts, since an account closed with no row cited passes |

Our predictions were wrong twice ("close around 90%, escalate around 80%"); the third ("as bad as the last run") held for Large 3. No change met the bar: the evidence score never went up.

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

We had planned a run B, giving Large 4 a summary of the account computed by code (one line per counterparty), in case it could not read a long table. We dropped it: run A showed that Large 4 did find the account's routine and the transactions that depart from it.

| | Large 4 | A: + method | C: + method, neutral alert | Claude (Nov 8) |
|---|---|---|---|---|
| normal accounts closed (of 16) | 0 | 1 (P21) | 1 (P19) | 14 |
| laundering accounts caught (of 16) | 16 | 16 | 16 | 11 |
| rows cited: laundering / other | 119 / 1,063 | 95 / 309 | 133 / 206 | 98 / 32 |
| evidence passed, single scheme (of 10) | 0 | 3 | 2 | 2 |
| rows cited on a typical normal account | 38 | 9 | 7 | 0 |

The method took: "structuring" fell from 28 of the 32 accounts to 2, and the rows from 1,182 to 404. The decision
did not move. Large 4's reasoning, saved for these runs, brings up the alert while deciding on 11 of the 16 normal accounts: "But given the alert, we flag the large outgoing transactions as suspicious" (P18); "But the alert is triggered, so I must find something suspicious" (P26). It brings up the instruction to flag suspicious rows on 11 as well, with the alert still there: "However, the prompt asks me to flag suspicious rows" (P21). With "flagged" removed, the alert falls to 5 and the instruction rises to 15: "But the prompt asks for suspicious rows. All are part of the scheme." (P21). Two things in the request imply that something is there to find, and it uses both; removing one leaves the other. These are counts of patterns in the saved reasoning, printed by `python report.py`; an earlier count by reading, in the notebook, found 11 accounts where it considered closing and 10 where it turned back on the alert. Claude got the same
alert and instruction and was not moved. The plan for these runs, written before them, is in [the notebook](NOTEBOOK.md#the-plan-for-the-method-run-as-written-before-it-nov-11).

**Not tested:** an instruction without "flag the suspicious rows" (it would change the original prompt, and these
are the same 32 cases every change was tried on, so each further prompt fits this simulator more than the task).

## 4. Limits

- **Synthetic data:** no real bank or person involved at all. The simulator has habits a bank might not have (daily identical payments, reinvestment transfers to self, very large amounts).
- **Public data:** public since 2023, so any model could have read how it behaves.
- **One account, 18 days:** an analyst's best signals (a monthly rhythm, the other accounts in the scheme) are out of reach. From within one account, a scatter-gather looks exactly like a fan-out.
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
- **Cost:** around 103,000 prompt tokens per run (around 3,200 per case: tables of ids and amounts cost many tokens). 8 runs of Small 4 and Large 3 at a few cents each. Large 4: 73,355 prompt and
  134,706 completion tokens at around $0.33, two harness reruns at around $0.35 each, the method and neutral-alert
  runs at around $0.40 each. Claude Opus 5.5: 103,549 prompt and about 16,500 completion tokens per run, around
  $0.75, four times.

## 5. What next, and what it costs

Each reading in the [README](../README.md#1-what-we-understood-about-mistral-large-4) names the test that would settle it. Beyond those:

1. **Claude on accounts it has not seen.** Its result held on four runs of the same 32 cases; that measures luck,
   not memory. New accounts from another of IBM's datasets reduce the risk only partly (those are public too); only regenerated or real data removes it.
2. **Better data:** the larger IBM datasets cover a longer period, so the monthly rhythm shows. A sample of
   anonymised alerts from one bank with the analyst's decisions as the key. That's the only real test of capacity.
3. **For the Mistral models:** a request that assumes nothing (no alert, and an instruction that does not ask it to "flag the suspicious rows"), on new cases, not these 32. If Large 4 then closes the false
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
