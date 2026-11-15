*The lab notebook, written during the work (Nov 7 to 9, 2026), in the third person: "her" is Bassma, whose words
are quoted as she wrote them; Claude (Claude Code) kept this record. The README is the write-up.*

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

## Large 4 with the analyst's method (Nov 11)

Prompted by reading the two models' reasons side by side (`REASONING.md`): Claude first says what the
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
