*The lab notebook, written during the work (Nov 7 to 15, 2026), in the third person: "her" is Bassma, whose words
are quoted as she wrote them; Claude (Claude Code) kept this record. The README is the write-up.*

## Entries

**Nov 7, reading and design**

- [Three reasons I would close an alert](#three-reasons-i-would-close-an-alert)
- [What one case can show](#what-one-case-can-show-her-answer-after-checking-the-case-format)
- [The question the eval answers](#the-question-the-eval-answers-her-sentence-for-the-top-of-the-memo)
- [Prompt (first thoughts, her words)](#prompt-first-thoughts-her-words)

**Nov 8, the first runs**

- [Predictions for mistral-small-2603, written while it ran](#predictions-for-mistral-small-2603-written-while-it-ran-nov-8)
- [The answer, for the memo](#the-answer-for-the-memo-her-words-nov-8-after-all-three-runs)
- [Blind cases](#blind-cases-7-minutes-for-the-four-written-before-opening-any-key)
- [The simulated-bank rerun](#the-simulated-bank-rerun-nov-8-written-before-the-run)
- [The objective rerun](#the-objective-rerun-nov-8-written-before-the-run)
- [The combined rerun](#the-combined-rerun-nov-8-written-before-the-run-the-last-prompt-change-on-these-32-cases)
- [Her reading of the four runs](#her-reading-of-the-four-runs-nov-8)
- [Mistral Large 4](#mistral-large-4-nov-8-written-before-the-run)
- [Claude Opus 5.5](#claude-opus-55-nov-8-written-before-the-run-her-request-as-an-outside-reference)
- [Her reading after the Claude run](#her-reading-after-the-claude-run-nov-8)

**Nov 9, the harness check**

- [The harness check: Large 4 with Claude's schema](#the-harness-check-large-4-with-claudes-schema-nov-9-written-before-the-run)
- [Large 4 with the schema at temperature 1](#large-4-with-the-schema-at-temperature-1-nov-9)

**Nov 11 and 12, the method**

- [The plan for the method run, as written before it](#the-plan-for-the-method-run-as-written-before-it-nov-11)
- [Large 4 with the analyst's method](#large-4-with-the-analysts-method-nov-11)
- [Large 4 with the method and a neutral alert](#large-4-with-the-method-and-a-neutral-alert-nov-11)

**Nov 15, reruns and direct questions**

- [Claude Opus 5.5, three reruns](#claude-opus-55-three-reruns-nov-15-written-before-the-runs)
- [Asking the models directly about laundering patterns](#asking-the-models-directly-about-laundering-patterns-nov-15-written-before-the-run)
- [Where the checks of Nov 15 came from](#where-the-checks-of-nov-15-came-from-her-observations-in-her-words)
- [Asking Large 4 to define the four patterns it did not name](#asking-large-4-to-define-the-four-patterns-it-did-not-name-nov-15-written-before-the-run)

# Field notes

## Three reasons I would close an alert

- **Gather-scatter (2c):** a company paying agencies and receiving money from clients, regular payments, similar
  amounts, account linked to known documented company account with legitimate business.
- **Fan-in (2b):** landlord receiving payments: same amounts each month from each account (maybe different amounts
  by account).
- **Random (2f):** could apply to many transactions, I wouldn't flag it if those same accounts don't appear multiple
  times in different combinations in other random patterns.

## What one case can show (her answer, after checking the case format)

I would need to see multiple accounts and bank transactions, specially for random. For landlord I can rely on their
account alone but I would need to see a wider date range, same for company.

*(The data covers Sep 1–18, 2022, and a case is one account's table: a limit for the memo.)*

## The question the eval answers (her sentence, for the top of the memo)

Can an LLM save time by closing flagged cases that are regular and facilitating escalation to the analyst?

(Why an LLM at all: detection is better done by graph models and gradient-boosted trees, as in the IBM paper's §4;
the LLM's possible job is the analyst's triage step after the alert fires.)

**Which mistake is worse (her answer):** "first mistake is worse so recall is a priority, but if it escalates
everything it's not doing anything additional to explaining to the analyst everything flagged by the model."
In the table: the escalate slice's pass rate is the recall (must stay high); the close slice's pass rate is the
share of false alarms closed, which is the time saved (the value).

## Prompt (first thoughts, her words)

- **Pattern names:** "I wouldn't give it here anyway. If we're looking at one account, I would simplify to how
  the patterns look inside one account instead of giving 8."
- **Instruction:** "see if it detects unusual/suspicious transactions or not, a decision to escalate or close, and
  why."
- **Alert:** one generic text for all cases, "so the test doesn't depend on which detector was used or how it was
  configured."
- **What the grader checks besides the decision:** the flagged rows.
- **Instruction, first draft:** "analyze this account's transactions for possible money laundering schemes, flag
  the suspicious transactions if any… or something like that."
- **Instruction:** analyze the account transactions for possible laundering, flag suspicious rows. Decision:
  escalate or close. List: ids of suspicious rows.
- **Format:** forced by the API (JSON mode), "I don't see any reason not to pick it."
- **A `reason` field:** yes, added (not graded; for the analyst and for reading failures). Its place in the JSON:
  open, see below.
- **Order:** reason first, "so the model reasons through the question instead of finding a justification after.
  But I've heard models usually already make their decisions even in this case?" (Faithfulness research: Turpin et
  al. 2023, Lanham et al. 2023. A possible experiment: run both orders and compare.)
- **Alert:** "This account has been flagged for suspicious activity."

## Predictions for mistral-small-2603, written while it ran (Nov 8)

Against the rule (30% / 93.8% / 10%): decision-escalate-single **higher**; decision-close **lower**;
rows-escalate-single **above 50%**.

**Result:** the small model escalated all 32 cases (decision-close 0%, every rows slice 0%), calling the repeated
identical payments "structuring or layering". Her reading: "it's thinking like me before I understood what to look
for."

**Model or simulator?** Her words: "it's giving good reasons that would make sense for real accounts, so I don't
know. Maybe it's realistic, I don't know what real accounts look like in a big bank."

## The answer, for the memo (her words, Nov 8, after all three runs)

On simulated alerts, the model is flagging every account. What it shows is that the simulated cases don't look like
normal realistic account transactions; it tells us nothing about the model's capacity on real accounts. We would
need more realistic data to determine that (maybe first simulated over longer periods, then real anonymized if not
conclusive).

**Corrected version** (her wording; the hypothesis phrasing, the cheap test and the two supporting facts are
Claude's corrections, which she agreed to):

On simulated alerts, both models flag every account: they closed 0 of 16 false alarms, so they saved the analyst no
time. The most likely cause is that the simulated cases don't look like realistic account transactions: the models'
reasons are sound by real-world standards, the large model did no better than the small one, and a ten-line rule
closed 15 of 16, so the false alarms can be told apart. It tells us nothing yet about the model's capacity on real
accounts. To check the cause, rerun the close cases with one sentence saying the bank is simulated (a few cents);
to determine real capacity, we would need more realistic data: first simulated over longer periods, then real
anonymized if not conclusive.

## Blind cases (7 minutes for the four, written before opening any key)

- **B01:** I wouldn't escalate.
- **B02:** I wouldn't escalate.
- **B03:** almost all transactions are the same every day, same amounts to same accounts, with one account getting
  three different amounts a day with different methods: that seems like a fan-out done over multiple days and
  methods in smaller amounts.
- **B04:** a very large transaction, T003, and multiple transactions only a few days apart to the same account with
  a credit card: T002, T005, T009, T011, etc.

**Final answers** (decision, rows, reason):

| case | decision | rows cited | reason |
|---|---|---|---|
| B01 | close | — | didn't see a pattern, not many transactions, in and out payments to different accounts mostly, not enough data to flag anything |
| B02 | close | — | same as B01 |
| B03 | escalate | all except T001 and T026 | a fan-out done over multiple days and methods in smaller amounts |
| B04 | escalate | T003, and the credit-card rows to the same account: T002, T005, T009, T011, etc. | a very large transaction, and repeated card payments a few days apart to one account |

**Score against the keys: 0 of 4 decisions right.** B01 was a CYCLE (attempt #72, rows T002, T004), B02 a
SCATTER-GATHER (attempt #227, rows T005, T007, T010); B03 and B04 were normal.

Her words after the keys: "I actually flagged regularity because I couldn't understand why there would be regular
payments every day with big amounts, but the laundering accounts didn't make regular wires. B1 makes sense as a
cycle, it's getting in and out close amounts 2 days apart, it could also be gather scatter but there is only two
transactions."

On B02, after printing the whole attempt #227: "it sits at the start, and the receiving accounts are in the middle,
makes a lot of sense with the full picture of transactions made from the receiving accounts." From inside the
account alone, the gather is invisible.

## The simulated-bank rerun (Nov 8, written before the run)

**Scope (her call):** all 32 cases, not only the 16 close ones: "in case it closes the laundering cases too." A
close-only rerun cannot tell a model that now reads the simulator correctly from one that now closes everything.

**Sentence added to the instruction** (`variants/simulated.txt`; her first draft, then Claude's rewording, which she
accepted): her draft was "these transactions are simulated over a short time frame, so regular payments to the same
accounts are normal". Used: "These transactions come from a simulated bank, over a short time frame. In this
simulation, regular payments of the same amount to the same accounts are normal customer behaviour."

**Prediction (her words, both models):** "close goes up to around 90% at least, escalate might drop a bit, maybe
around 80%."

**Result (Nov 8):** no change. Both models again escalated all 32: decision-escalate 100% (single and hub),
decision-close 0%, every rows slice 0% (Large lost its one evidence pass, P04). Tokens: 32 calls per model, 103,484
prompt (1,056 more than Nov 8, so 33 tokens per call: the sentence was in every prompt); completion 7,636 (Small),
6,987 (Large). Her reaction: "No improvement, surprising."

What the reasons say (read by Claude in `results/*+simulated.json`): on the close cases, both still call the regular
identical payments "structuring or layering", the behaviour the sentence calls normal. Small on P31: "highly
repetitive transactions … which is unusual for regular customer behavior." Some reasons move to the other simulator
habits the sentence did not mention: very large amounts (P18, P27, P32) and big self-reinvestments (P17, P20).

## The objective rerun (Nov 8, written before the run)

**Her reading of the 0% after the simulated rerun:** maybe the sentence got less attention where it sat ("it might
need to be included in the row"), "or maybe we need to tell the model that the objective is to filter out false
alarms." The objective is tested first; the position test can follow as its own run.

**Change, against Nov 8 (the simulation sentence dropped):** one sentence after the format instructions
(`variants/objective.txt`). Her draft: "your objective is to dismiss false alarms without missing any real one to
reduce the workload for the next analyst." Used, after Claude's two suggestions, which she accepted ("close" for
the decision's own word; "without missing any real one" dropped, since for an unsure model it still points to
escalating everything): "Your objective is to close false alarms, to reduce the workload for the next analyst, and
to escalate real cases."

**Prediction (her words, both models):** "same predictions I gave before": close around 90% at least, escalate
might drop a bit, around 80%.

**Result (Nov 8):** Large unchanged (escalated all 32; evidence 1 of 10 on single schemes again, P04). Small moved
the wrong way: it closed 1 normal account (P32) and 3 laundering ones (P09 scatter-gather hub, P12 bipartite, P16
random hub): decision-close 6%, escalate-single 90%, escalate-hub 67%. Tokens: 32 calls per model, 103,196 prompt;
completion 6,607 (Small), 7,434 (Large).

What the reasons say (read by Claude): Small's four CLOSE answers use the same regularity it calls structuring
elsewhere, read the other way: "could indicate structuring or layering. However, the amounts are consistent…". On
P32 it answered CLOSE and still cited 20 rows.

## The combined rerun (Nov 8, written before the run; the last prompt change on these 32 cases)

**Change, against Nov 8:** both sentences, the simulation one then the objective one (`variants/both.txt`).
**Bar for "it works"** (Claude's proposal; she went ahead with it): close goes up, escalate stays at or near 100%,
and evidence on the escalate slices rises above 10%. Close up with evidence at 0% means the threshold moved, not
that the model sees the laundering.
**Prediction (her words):** "I predict it's gonna be as bad as the last run."

**Result (Nov 8):** Large unchanged again (escalated all 32; evidence P04 only). Small swung to closing: it closed 11
of 16 normal accounts (decision-close 69%), but also 6 of 10 single-scheme and 4 of 6 hub laundering accounts
(escalate 40% and 33%); evidence 0% on every escalate slice. Below the bar: close rose, escalate fell, evidence did
not move. Tokens: 32 calls per model, 104,252 prompt; completion 3,175 (Small), 6,200 (Large).

What the reasons say (read by Claude): Small swapped one surface feature for another. Regular payments now read as
"normal customer behavior" (it closed P01, P10, P12, P16 laundering with that phrase); it escalates on very large
amounts or large self-transfers instead (P03, P04, P08, P13, P14; and normal P18, P23, P27). The prediction "as bad as
the last run" holds for Large; for Small the score moved, but the bar was not met.

## Her reading of the four runs (Nov 8)

"I think the model is looking for weird patterns based on regular accounts, even I couldn't find the weird patterns
just from one account until you told me what they looked like (one off payments inside regular ones)."

**Corrected version** (her reading; the joins and the consequence for the next test are Claude's): in all four runs
the models judged each account by what looks unusual in a real bank: first regular identical payments, then, once
told those are normal, very large amounts. In this data the laundering is two or three one-off payments inside an
otherwise regular account. I could not see that from one account either, until I was shown what it looks like. So a
sentence about the data or the objective is not enough: the model would need to be told or shown that pattern, and
that has to be tested on new cases, not on these 32.

## Mistral Large 4 (Nov 8, written before the run)

Same cases and prompt as the first run (no variant), only the model changes: `mistral-large-4`, Mistral's newest
model. The runs so far were Small 4 (`mistral-small-2603`) and Large 3 (`mistral-large-2512`).
**Prediction (her words):** "they're gonna be almost as bad."

**Result (Nov 8):** exactly as the first run of the other two: escalated all 32, decision-close 0%, every evidence
slice 0% (on P04, the one case Large 3 passes, it cited 5 rows including normal ones). Tokens: 32 calls, 73,355
prompt (a different tokenizer), 134,706 completion: about 4,200 per case, so it reasons before answering, and it
was slow. About $0.33 at $0.70 / $2.10 per million. Reasons: "classic structuring/smurfing" on every close case,
the same reading as the others. Her prediction "almost as bad" held, and then some.

## Claude Opus 5.5 (Nov 8, written before the run; her request, as an outside reference)

Same cases and prompt as the first run; `claude-opus-5-5`. Differences, set in `system.py`: the format forced by a
schema (decision limited to ESCALATE or CLOSE), no temperature setting (one run at normal randomness), reasoning at
its default level, a refusal counted as an infra error (no automatic fallback to another model).
**Prediction (her words):** "same results."

**Result (Nov 8):** very different from every Mistral run. Decision-close 88% (14 of 16 normal accounts closed),
escalate 80% single (8 of 10) and 50% hub (3 of 6); evidence 20% single, 17% hub, 88% close. Tokens: 32 calls,
103,549 prompt, 16,455 completion (about 500 per case: little reasoning at the default level). About $0.74 at $4 / $20
per million. No infra error, no refusal. Her prediction "same results" did not hold.

What the reasons say (read by Claude): it reads the accounts the way she learned to after the keys. Regular
identical payments are "routine recurring payments"; it escalates on one-off items inside them: a burst of credits
from new counterparties (P06, P08), a self-conversion then a payout in another currency (P03, P04, P10, P13), three
payments in minutes in three formats (P09, P12). Missed: P01 and P02 (cycles, two quiet rows each) and three hubs
(P11, P14, P16), read as "related-entity treasury transfers". Wrongly escalated: P28 ("just under a 10k threshold")
and P32 (a one-off cheque from a new counterparty, then three fast payments).

Caveats to keep: one run at normal randomness, not temperature 0; the format forced by a schema; IBM's dataset has
been public since 2023, so the model may have seen descriptions of it; a different company's model, tested once.

## Her reading after the Claude run (Nov 8)

1. "It might be the model, can't conclude on data, but it might also be that Claude saw these before as well, and
   yes temp was not 0."
2. For a memo to Mistral: "not a weakness to hide, a gap maybe, but I would still use better data."

## The harness check: Large 4 with Claude's schema (Nov 9, written before the run)

Raised at her request after reading "The Harness Is the Model" (arXiv 2611.06116): Claude's run differed in
format (schema), randomness (no temperature) and reasoning. Large 4 already reasons by default (about 4,200 output
tokens per case), so this run changes only the format: same prompt and cases, temperature 0, Claude's schema instead
of JSON mode (`run.py mistral-large-4 schema`). Her choice of Large 4 over Small 4: one change, not two.
**Prediction (her words):** "same perf this run with temp 0." Her question: "shouldn't we change temperature?"

**Result (Nov 9):** her prediction held. Identical to the first Large 4 run: escalated all 32, decision-close 0%,
evidence 0% everywhere. Tokens: 32 calls, 75,339 prompt (1,984 more than the first run, 62 per call: the schema was
sent), 142,781 completion. About $0.35. The format does not explain the gap.

## Large 4 with the schema at temperature 1 (Nov 9)

Same as the schema run, temperature 1 instead of 0 (her choice: no Claude credits left for the reruns). No
prediction written before this one. **Result:** escalated all 32 again, decision-close 0%; evidence 10% on single
schemes (one case), 0% elsewhere. Tokens: 32 calls, 75,339 prompt, 138,796 completion; about $0.34. Randomness does
not make Large 4 close anything. Still open: whether Claude's 88% holds on a rerun (needs credits).
She stopped here (Nov 9).

## The plan for the method run, as written before it (Nov 11)

These are the same 32 cases every earlier prompt change was tried on, so a fourth prompt would fit this simulator,
not the task. The run is a diagnostic, to locate the gap, not a new score; a score needs fresh cases.

The earlier variant runs *told* the models that regularity is normal; they swapped one feature for another and kept
the same method. This run asks Large 4 to *find* the normal itself, with Claude's method in the prompt and nothing
else changed. Two runs separate three explanations:

| run | what Large 4 gets | if it now closes normal accounts, the gap was… |
|---|---|---|
| A | the method in the prompt (`src/variants/method.txt`) | its default way of working: it had the skill and applied the wrong procedure |
| B, only if A fails | the method, plus a summary computed by code, one line per counterparty (payments, total in and out, first and last date) | reading a long table: it cannot build the baseline over 100+ rows, but reasons fine once given it |
| neither works | | deeper: how it reasons about this domain, or what it believes about laundering |

What each would mean for improving the model:
- **A works:** the model knows how but does not do it by default. It reaches for textbook labels it learned
  elsewhere over the evidence in front of it. A post-training fix (analyst-style examples, or a reward for closing
  false alarms), not a bigger model.
- **B needed:** a weakness in pulling a pattern out of a long table. A tool (code over the rows) or training on long
  tables; better instructions will not help.
- **Neither:** a reasoning or knowledge gap, the most expensive kind to fix.

Three cautions:
- **The bar is Claude, not 16 of 16.** Claude's method misses hub accounts where the laundering is the routine
  (P11, P14, P16). A Large 4 that copies it well should miss them too.
- **The method may only fit this dataset.** "Routine is normal" may be how IBM's simulator makes normal accounts.
  A success shows the method works here; the rearranged-routine test (same accounts, new amounts and dates,
  laundering rows kept) would show whether it works in general. The same test would tell whether Claude worked its
  method out or knows IBM's data.
- **Score the rows, not only the decision.** A Large 4 that closes normal accounts but still cites 40 rows per
  laundering account has changed its answer, not its method.

## Large 4 with the analyst's method (Nov 11)

Prompted by reading the two models' reasons side by side (`REASONING.md`, since split between `REPORT.md` and `ANSWERS.md`): Claude first says what the
account normally does and escalates on what departs from it; Large 4 never describes normal and calls repetition
"structuring". Run A adds that method to the instruction (`variants/method.txt`, `run.py mistral-large-4 method`),
nothing else changed. Run B, only if A falls short: the same, plus a summary per counterparty computed by code.
Same 32 cases as every earlier prompt change, so this is a diagnostic (where the gap is), not a score.
**Prediction (her words):** "large 4 will do better but less good than claude with A alone, and maybe like claude
with B". Her reason: in her earlier experiment (`the-data-cant-tell`), handing Large 4 figures computed by code took
it from 4 to 9 fully right answers out of 10.

**Result (Nov 11, run A).** Decisions barely moved: escalated all 16 laundering accounts and 15 of 16 normal ones
(closed only P21; decision-close 6% against 0% before and Claude's 88%). The method itself took: on the normal
accounts, "structuring" in 3 reasons instead of 15 and the routine described in 9 instead of 1; rows cited fell from
1,182 to 404 (95 laundering rows, 309 others; Claude 98 and 32), with a median of 9 rows on a normal account instead
of 38; the rows test passed on P03, P04 and P15 (three, as many as Claude). Tokens: 32 calls, 76,011 prompt,
170,057 completion, about $0.40. The reasoning is saved for the first time (`results/mistral-large-4+method.thinking.json`).
**What the reasoning shows:** it follows the three steps, and on 11 of the 16 normal accounts it considers closing.
On 10 of them it then turns back on the alert itself: "But given the alert, we flag the large outgoing transactions
as suspicious" (P18); "But wait - the account is flagged for suspicious activity" (P21, the one it closed anyway).
It also calls money "passing through" when the figures do not show it (P31: nothing comes in from anyone, only a $1.1M self-reinvestment, while $92M goes out).
So the gap left is not reading the table but how much weight the alert gets: "flagged" is read as evidence.

## Large 4 with the method and a neutral alert (Nov 11)

Her call after run A: drop run B ("I don't think B is worth it"), since the reasoning showed Large 4 found the
routine and the departures, then fell back on the alert. Instead, one change on top of run A: the line
"Alert: This account has been flagged for suspicious activity." becomes "This account was selected for review."
(`run.py mistral-large-4 method-neutral`). Her reading: "This is your own finding from The Data Can't Tell, showing up
again: exactly", the alert, like "why did X drop?", carries a hidden assumption. "If large4 does better it's a great
insight for training." The instruction is unchanged, so two milder cues stay: "flag the suspicious rows" and
"CLOSE (a false alarm)".
**Prediction (her words):** "it does better than the last run".

**Result (Nov 12).** Her prediction did not hold on the decision: the same as run A, all 16 laundering accounts
escalated and 15 of 16 normal ones (it closed P19 this time, and escalated P21, which run A closed). The rows
improved again: 339 cited, 133 laundering rows (Claude 98, run A 95) and 206 others (run A 309, Claude 32), a median
of 7 on a normal account; rows test passed on 2 of the 10 single-scheme accounts. One request timed out and was
retried (P01). Tokens: 32 calls, 75,851 prompt, 176,120 completion, about $0.40.
**What the reasoning shows:** the alert no longer appears as a reason (the neutral line is quoted once, on P21). The
instruction takes its place: on 13 of the 16 normal accounts the reasoning quotes "flag the suspicious rows" while
deciding, for example "But the prompt asks for suspicious rows. All are part of the scheme." (P21). It still
considers closing on 12 of 16. Remove one cue that the account is suspicious and it leans on the next one.

## Claude Opus 5.5, three reruns (Nov 15, written before the runs)

The Nov 8 run is the only Claude run: 14 of 16 normal accounts closed, 11 of 16 laundering accounts caught, once,
with the API's default randomness. Three more runs of the same request on the same 32 cases
(`claude-opus-5-5 repeat2`, `repeat3`, `repeat4`), to see whether that result holds. Nothing in the request
changes. New in the record: the tokens Claude spends reasoning on each case, which the API reports and the first
run did not save. This tests luck, not memory: the cases are the same, so a model that had seen the data would
still have seen it.
**Prediction (her words):** "about the same 13-15" normal accounts closed, of 16. No prediction given for the
laundering accounts.
**What would change the reading:** a run under 12 of 16 closed, or runs that spread widely, would mean the single
run overstated the gap.

**Result (Nov 15, three runs, 18:48 to 18:56).** Her prediction held: 14 of 16 normal accounts closed in each of
the three reruns, as on Nov 8. Laundering accounts caught: 11, 11 and 12 of 16 (Nov 8: 11); hubs 3 of 6 every
time. No failed call, no retry. Tokens per run: 103,549 prompt, 16,323 / 16,367 / 17,165 completion.
**The totals are stable, six cases are not.** 26 of the 32 cases got the same decision in all four runs. Six
changed sides at least once: the laundering accounts P01, P02 (the two cycles), P03 and P04, and the normal accounts
P17 and P28. P17, the worked example of the memo, was closed on Nov 8 and escalated in all three reruns; P28 was
escalated on Nov 8 and closed in all three. Wrong in all four runs: the hubs P11, P14 and P16, and the normal
account P32. Evidence passed on 3, 2, 3 and 4 of the 16 laundering accounts; rows cited, laundering / other: 98 / 32,
77 / 33, 56 / 25, 107 / 31.
**Reasoning, measured for the first time.** Claude reasoned on 29, 30 and 30 of the 32 cases and answered the
others directly (P19 and P24 every time, P11 once). Reasoning took about 11,200 to 11,800 of its output tokens per
run, about 350 per case, at most 779 on one case.
**What it does not show.** The same 32 cases four times are not 64 independent cases: this measures how much
Claude's answers vary, not whether it has seen the data. Fresh accounts are still the test for that.

## Asking the models directly about laundering patterns (Nov 15, written before the run)

On the 32 cases, no Mistral run names one of the dataset's network patterns (fan-out, fan-in, scatter, gather,
stack, bipartite: zero times in the answers and in the saved reasoning); they use the cash vocabulary
(structuring, layering, smurfing, placement). Claude names the network patterns, and where it asserts one it
matches the key (P03 fan-out, P06 fan-in, P08 fan-in then fan-out, P10 fan-out). Two explanations for the Mistral
models: they do not know these patterns, or they know them and a case does not call them up.
**The probe** (`probe.py`): two questions, no account, no alert, no system message, neither naming a pattern.
Open: "What are the common patterns of money laundering?" Network: "What patterns of money laundering can be seen
in a network of transactions between bank accounts?" Four models: Small 4, Large 3, Large 4 at temperature 0, and
Claude Opus 5.5. One call per question.
**What is counted, fixed before the run** (`src/vocabulary.py`): which of the eight patterns each answer names
(fan-out, fan-in, cycle, scatter-gather, gather-scatter, stack, bipartite, random) and which cash terms
(placement, layering, integration, structuring, smurfing). The answers are also read, since a shape can be
described without its name, and "stack" and "random" are ordinary words.
**How it will be read:** most of the eight named on the network question means the knowledge is there and the case
does not call it up; none or one, with cash terms, means it is not there; shapes described without the names is
in between.
**Prediction (her words):** "I predict question 2 to list everything, question 1 to be about cash stages."
*Clarified by her after launching the run and before reading any answer:* that prediction was for the Mistral
models. For Claude: "I expect it to give the patterns in both + maybe cash."

**Result (Nov 15, 20:22, one call per question).** Counted with the lists fixed before the run, then read.
- **Open question:** all four models, Claude included, answer with the cash framework (placement, layering,
  integration, structuring) and name none of the eight network patterns. Her prediction held for the Mistral
  models. For Claude it did not: she expected the patterns in both answers.
- **Network question:** Claude names 7 of the 8, with the dataset's own names (fan-out, fan-in, scatter-gather,
  gather-scatter, cycle, bipartite, stack), in a numbered list of eight "structural (topological) patterns". Large 4
  names 3 (fan-in / fan-out in one line, and cycles). Large 3 and Small 4 name 1 (circular flows). Her prediction
  "list everything" did not hold for the Mistral models.
- **Read, not counted:** the Mistral models describe the shapes without the names. Large 3: "chain structures",
  "star or hub-and-spoke networks", "mesh networks". Small 4: "star-like subgraphs", "long, winding transaction
  chains", "high-degree nodes". Large 4: "funnel accounts", which is a gather-scatter in other words.
- **How each answer is organised, on the network question:** the three Mistral models still build the answer on
  the cash framework. Small 4's headings are Structuring, Layering, Integration; Large 3's are Layering,
  Integration; Large 4's open with "Classic structuring patterns" and "Layering patterns", and fan-in / fan-out is
  one line under layering. Claude's first heading is "Structural (Topological) Patterns".
**Reading.** Not "missing" and not "there but unused", in between, and different per model. Large 4 knows fan-in,
fan-out and cycles by name and never used them on 160 case answers: for those, the case does not call them up.
All three Mistral models know the shapes; none has the dataset's vocabulary beyond that. And even when asked about
networks, they organise what they know by the cash stages.
**What this does not show.** One call per question, one wording: another wording could give other lists. That
Claude reproduces the dataset's taxonomy almost name for name shows it knows the literature the data comes from;
it does not show that it has seen the data.
*Her note:* the eight patterns are ones we read about before building the cases, not something the data alone
defines. *Checked afterwards:* her Nov 7 reading notes cite them by their figure labels, (2b), (2c), (2f): that is
Figure 2 of the dataset's paper (Altman et al., 2023, arXiv:2306.16424). Its section 3.2 says where the set comes
from: "In their AMLSim generator, Suzumura and Kanezashi introduced a set of 8 patterns often used in money
laundering." So the eight, as a set and with these names, come from that line of work; fan-in, fan-out and cycle
are also general terms.

## Where the checks of Nov 15 came from (her observations, in her words)

Each check run on Nov 15 started from something she noticed or questioned. Her words, as she wrote them.

- **The vocabulary.** Reading the answers: "I noticed claude mentions terms like "fan-out" and the patterns I saw
  while reading wikipedia and the article when I first started this case, large 4 mentions different terms like
  "layering" and something else?" This led to the count of terms per run, then to asking the models directly.
- **Not jumping to "Claude has seen the data".** On Claude's use of the pattern names: "that is a bold claim, we
  have seen these terms outside of IBM's dataset". The check that followed separated the three general terms from
  the four particular to the dataset's literature.
- **Method is not knowledge.** When Claude wrote that giving Large 4 the method gave it the knowledge: "isn't it
  giving it the reasoning? it still didn't name the laundering patterns (fan out, gather scatter, etc.)". And on
  the cause as first written: "also the knowledge no? with today's finidngs?"
- **The direct question.** "let's ask Large 4 directly to list laundering patterns in transaction networks then".
- **Findings are not insights.** On a first list of results: "these are findings, good ones, not insights about
  the models like the one about large giving emphasis to the framing or assumptions in the prompt". The section
  of readings in the README comes from that distinction.
- **Weakness, or a different approach.** On the readings: "I'd say some claims are about model "weakness" while
  others are about different approach from claude, which I can't know if it's good in some other cases outside of
  our benchmark". The readings are now split that way.
- **The framing as evidence.** Her reading of Nov 14, "it treats what the request presupposes as evidence", was
  tested on the saved reasoning: the alert is brought up while deciding on 11 of the 16 normal accounts, the
  instruction on 11. Her words on seeing it: "the additional rows you found are very interesting and confirm my
  instinct".
- **The baseline rule.** ""paid 8 or more different accounts within 3 days" sounds a bit random". This led to
  scoring the rule at other thresholds; it stays as it was, fixed before the runs.
- **A run that stops.** While the reruns were going: "if we run out of tokens mid run, we lose everything". Runs
  are now saved line by line and can be resumed.
- **Still open, by her:** "but it could still be missing knowledge no? I don't know". The next entry tests it.

## Asking Large 4 to define the four patterns it did not name (Nov 15, written before the run)

Asked what laundering patterns can be seen in a network of transactions, Large 4 named fan-in, fan-out and cycles,
and not scatter-gather, gather-scatter, bipartite or stack. Either it does not know those four, or it knows them
and did not list them. The first question tested recall; this one tests recognition.
**The questions** (`python probe.py definitions mistral-large-4`), one call each, temperature 0, no system message:
"In money laundering through bank transactions, what is a scatter-gather pattern?", and the same for
gather-scatter, bipartite and stack. A fifth question asks for a "hinge-loop" pattern, which does not exist: if
Large 4 defines that one too, its other definitions show fluency, not knowledge.
**What counts as a correct definition, fixed before the run,** from the dataset's paper (Altman et al., section
3.2): scatter-gather, a fan-out from one account and a fan-in to another through the same intermediate accounts;
gather-scatter, a fan-in and a fan-out at the same account; bipartite, funds moved from a set of input accounts to
a set of output accounts; stack, a bipartite pattern with one more layer. AMLSim's own documentation gives the two
compound patterns in the same shapes. An answer is correct if it describes that shape, whatever its wording.
**Prediction (her words):** "I predict it defines them".

**Result (Nov 15, 22:22, five calls).** Judged against the definitions fixed above.

| asked to define | the shape it describes | correct | how it frames it |
|---|---|---|---|
| scatter-gather | a large sum split into many small transactions, then recombined in one account | yes | "often called smurfing or structuring"; amounts "kept below regulatory reporting thresholds" |
| gather-scatter | many deposits into one account, then dispersed to many recipients | yes | "sometimes called smurfing"; each deposit "below a reporting threshold" |
| bipartite | funds between "two distinct, separate groups of accounts", with little activity inside each group | yes | in graph terms, then "smurfing/structuring" among what it indicates |
| stack | deposits each below a reporting threshold, "stacked" into a larger balance | no: the paper's stack is a bipartite pattern with one more layer | structuring |
| hinge-loop (invented) | funds that "repeatedly leave and return through a common hinge account" | there is no such pattern | it says the term "is not one of FATF's standardized typology labels", then defines it anyway |

Her prediction, "it defines them", held on the shape for three of the four, and not for stack.
**What the control changes.** Large 4 also defined a pattern that does not exist. So a correct definition is not
proof that it knew the pattern: "scatter-gather" and "gather-scatter" can be worked out from the words, and
"bipartite" is a general term for graphs. "Stack" cannot be worked out from the word, and it is the one it got wrong.
**Reading.** Two things, both sharper than before. All five answers, the invented one included, come back to
structuring under reporting thresholds: given a network pattern by name, Large 4 still explains it as a way of
splitting cash. And it probably does not know the dataset's own taxonomy as such; her doubt, "it could still be
missing knowledge", is supported for that taxonomy. It is not missing the general idea of network patterns, which
it named unprompted in the earlier question.
**What this does not show.** One call per question. Whether knowing that taxonomy would change its decisions on the
cases is a separate question, which the test in the README's fourth reading would answer.

