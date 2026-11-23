# Can a language model reduce the number of false positives in AML alert queues?

*This is a summary of a very small benchmark: 32 flagged accounts from IBM's synthetic bank, a rule baseline, three Mistral models, and Claude Opus 5.5 as an external reference. The full record, with each prediction written before its run, is in [`NOTEBOOK.md`](docs/NOTEBOOK.md).*

**The decision.** Whether to put a language model in front of the alert queue. It would filter out clear false alarms and pass the rest to an analyst, with the transactions that matter.

**The test.** A bank's monitoring system flags accounts, and an analyst decides whether to escalate each one or
close it as a false alarm. We took 32 accounts from IBM's synthetic bank data, 16 laundering and 16 normal, showed
each to the model as flagged, and scored its decision and the transactions it cited.

**The result.** The Mistral models, as tested, did not reduce false positives: all three (Small 4, Large 3, and
Large 4) escalated every account and closed none of the 16 false alarms. For comparison, we tested Claude Opus 5.5
four times on the same cases: each time it closed 14 of 16 false alarms and caught 11 or 12 of 16 laundering
accounts. So the task can be done from a single account, and the gap lies with the models.

**The caveat.** Claude did not come to this test cold. Asked what laundering looks like in a network of
transactions, it names seven of the eight patterns this data is built from, including the four particular to the data's own literature (scatter-gather, gather-scatter, bipartite, stack). So it knows
that literature; we cannot tell whether it has seen these accounts. The data is synthetic, and 32 cases can show a
large gap, not a small one. Firm conclusions need more testing, on more realistic data.

## 1. What we understood about Mistral Large 4

Four readings of how Large 4 works, the model we looked at most closely. They are interpretations, not
measurements: each says what it rests on, how sure we are, and what would test it further.

**Two failure modes.** These would be errors on any data.

| | what Large 4 does | what we saw | how sure | what would test it further |
|---|---|---|---|---|
| **1** | **It treats what a request presupposes as evidence.** | While deciding, its saved reasoning brings up the alert on 11 of the 16 normal accounts ("But the alert is triggered, so I must find something suspicious", P26) and the instruction to flag suspicious rows on 11. With "flagged" removed from the alert, the alert falls to 5 and the instruction rises to 15. The same effect in [a second experiment](https://github.com/BassmaSH/the-data-cant-tell), where "why did X drop?" made models find a drop. | Medium to high. Another reading fits: it would escalate anyway, and the cue is a justification written afterwards. | A request with no cue at all, on new cases: no alert, and an instruction that does not ask it to flag rows. |
| **2** | **It applies what is generally true of laundering, without first working out what is normal for this account.** | It calls routine payments "structuring" on 28 of 32 accounts, and on P11 cites a real Saudi cash-declaration threshold that the case never mentions. Asked to describe the account's normal first, "structuring" falls to 2 of 32. Published guidance for analysts says to start from the customer's normal. We made the same mistake on four blind cases (0 of 4). | Medium to high: it can do the step when told, and does not do it unprompted. | Cases where a textbook red flag is present and benign, without the method. |

**Two differences from Claude.** They cost Large 4 on this benchmark. Whether they would on other data is not
shown: here the laundering is built as network patterns, and Claude knows the literature those patterns come from.

| | what Large 4 does | what we saw | how sure | what would test it further |
|---|---|---|---|---|
| **3** | **For it, unusual is enough.** | Given Claude's method, it describes the account's routine and picks the same one-off row as Claude (P27), citing a third of the rows it cited before. It still escalates 15 of the 16 normal accounts: what departs from normal is treated as suspicious. Claude asks one more thing, whether the money moved on. The stricter test has a price: Claude misses 4 or 5 of the 16 laundering accounts, Large 4 none. | Low to medium: two accounts read closely (P27, P17); the totals fit. | Give it that one further test, without the method, and count both kinds of error. |
| **4** | **Its default frame for laundering is the cash framework, and it mostly keeps it when asked about networks.** | On the cases, it never uses a network term (fan-in, fan-out), in five runs; it says "structuring" and "layering". Asked directly about transaction networks, it does name the three general ones (fan-in, fan-out, cycles), under headings that are still the stages of laundering cash. It does not give the four names particular to this data's literature, which Claude gives. Asked to define those four, it describes the right shape for three and a wrong one for "stack", and explains all of them as structuring under reporting thresholds. | Medium on the frame: every answer comes back to cash thresholds. On knowledge: it probably does not know this data's taxonomy as such. It also defined a pattern we invented, so a correct definition is not proof. Each question was asked once. | Ask it to analyse the account as a network of counterparties, without the method, and see whether its decisions move. On data built around cash deposits, its frame may be the better one. |

Taken together: Large 4 decides from what the request implies and from what looks unusual, read through a
framework that does not fit this data.

The evidence is in the [full report](docs/REPORT.md): [what each model does](docs/REPORT.md#2-what-each-model-does) for readings 2, 3
and 4, and [testing the cause](docs/REPORT.md#3-testing-the-cause) for reading 1. Small 4 and Large 3 fail the same way on
the main result; on Small 4, prompt changes moved which feature it decides from and not its method
([the report](docs/REPORT.md#3-testing-the-cause)).

## 2. What is measured, and what is not

32 flagged accounts from IBM's synthetic bank (Sep 1–18, 2022): 16 laundering, 16 normal (8 drawn at random, 8
chosen from 15 candidates because they look most like an alert). The model sees one account's transactions and a generic alert, and answers in JSON: a reason, ESCALATE or CLOSE, and the ids of the suspicious rows. Two scores per account: the **decision** and the **evidence** (laundering account: more than half of the laundering rows cited and no normal row; normal account: no row cited).

It measures the first step of an analyst's work: one account, one decision, the rows that justify it. It does not
measure following money across accounts, working an alert over weeks, or performance on a real bank's data.

## 3. Result

Runs of 8th November 2026, same prompt for each model; answers in `results/`.

| slice | n | rule (no model) | `mistral-small-2603` | `mistral-large-2512` | `mistral-large-4` | `claude-opus-5-5` |
|---|---|---|---|---|---|---|
| decision: escalate, single scheme | 10 | 30% | 100% | 100% | 100% | 80% |
| decision: escalate, hub account | 6 | 17% | 100% | 100% | 100% | 50% |
| **decision: close (the time saved)** | 16 | **94%** | **0%** | **0%** | **0%** | **88%** |
| evidence: escalate, single scheme | 10 | 10% | 0% | 10% | 0% | 20% |
| evidence: escalate, hub account | 6 | 0% | 0% | 0% | 0% | 17% |
| evidence: close | 16 | 94% | 0% | 0% | 0% | 88% |

Settings: the Mistral models at temperature 0 in JSON mode; Claude with no temperature setting and its format
forced with a schema. Large 4 reasons before answering; Claude decides for each request whether to.

**Human review:** 0 of 4 decisions right on four blind cases, in 7 minutes, before learning what this data looks
like.

The rule escalates an account that paid 8 or more different accounts within 3 days. A model that always says
ESCALATE scores 100% on the escalate slices and 0% on close: the three Mistral models scored exactly that. The rule
fails the other way: it closes almost everything, laundering included, so it is a floor.

**Claude, the same request four times** (Nov 8, and three reruns on Nov 15; the table above shows the first):

| | Nov 8 | rerun 1 | rerun 2 | rerun 3 |
|---|---|---|---|---|
| normal accounts closed (of 16) | 14 | 14 | 14 | 14 |
| laundering caught, single scheme (of 10) | 8 | 8 | 8 | 9 |
| laundering caught, hub (of 6) | 3 | 3 | 3 | 3 |

26 of the 32 cases got the same decision in all four runs; six changed sides at least once ([which ones](docs/REPORT.md#2-what-each-model-does)).

**How sure are these scores?** With 16 normal accounts, each score has a wide range (exact 95% intervals):

| decision | rule | Small | Large 3 | Large 4 | Claude |
|---|---|---|---|---|---|
| close, of 16 | 15 · 70–100% | 0 · 0–21% | 0 · 0–21% | 0 · 0–21% | 14 · 62–98% |
| escalate, single scheme, of 10 | 3 · 7–65% | 10 · 69–100% | 10 · 69–100% | 10 · 69–100% | 8 · 44–97% |
| escalate, hub account, of 6 | 1 · 0–64% | 6 · 54–100% | 6 · 54–100% | 6 · 54–100% | 3 · 12–88% |

On closing, the ranges of Claude and the Mistral models do not overlap. Case by case, on the same 16 normal
accounts, Claude closed 14 that Large 4 escalated and Large 4 closed none that Claude escalated (exact McNemar
test, p = 0.0001). On catching laundering the ranges overlap: Large 4 caught 5 accounts that Claude missed and
Claude none that Large 4 missed (p = 0.06), which 16 cases cannot settle. The solid result is the gap on closing.

The gap does not come from the setup: Large 4 rerun with Claude's answer format, then with normal randomness, gave
the same result ([the check](docs/REPORT.md#1-is-it-the-harness)).

## 4. Limits, in short

- **Synthetic data:** no real bank or person involved at all.
- **Public data:** public since 2023, so any model could have read how it behaves.
- **One account, 18 days:** an analyst's best signals (a monthly rhythm, the other accounts in the scheme) are out of reach.
- **32 cases:** each close case is 6 points on its slice.
- **Not identical settings:** Claude's format was forced by a schema, the Mistral models by JSON mode, and the
  reasoning effort was left at each API's default.

The full list, with costs, is in [the report](docs/REPORT.md#4-limits).

## 5. Read more

| document | what it is |
|---|---|
| [`docs/REPORT.md`](docs/REPORT.md) | the full report: the check on the setup, what each model does case by case, the tests of the cause, the limits, what to do next, the timeline |
| [`docs/NOTEBOOK.md`](docs/NOTEBOOK.md) | the record of the work as it happened: each prediction written before its run, then the result |
| [`docs/ANSWERS.md`](docs/ANSWERS.md) | what Claude and Large 4 answered on each of the 32 accounts, generated from `results/` |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | the conventions of the code and how each is checked |

## 6. Reproduce it

```bash
python report.py                        # the tables above, rebuilt from results/, no API call
pytest -q                               # 52 checks, no API call (pip install pytest)
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

Each run prints the per-slice table and saves every answer in `results/`. Since Nov 15, 2026, a model run
also stores `<name>.meta.json` (the settings, the prompt as sent, the date, the library versions and the tokens per
case); the runs of Nov 8 to 12 were made before that. `benchmark/golden.jsonl` has two lines per case (the decision and the evidence), generated by `prep/make_golden.py` from `benchmark/cases/` and
`benchmark/keys/`. `src/aml_graders.py` does the scoring. The runner in `src/evals_kit/` is a copy of
[evals-kit](https://github.com/BassmaSH/evals-kit).

**Is the scoring itself right?** 52 tests, 21 of them on the two scoring rules; and `report.py` grades every saved
answer again before printing a table, so the numbers above follow from the answers and the scoring code as they are
in the repo today. Conventions for changing the code are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

**The data.** IBM's synthetic anti-money-laundering data, split HI-Small (Altman et al., *Realistic Synthetic
Financial Transactions for Anti-Money Laundering Models*, NeurIPS 2023, <https://arxiv.org/abs/2306.16424>), licence
CDLA-Sharing-1.0. Everything is simulated, no real person or real bank. The raw files are not in this repo;
`prep/README.md` says how to rebuild them and `prep/make_case.py` cuts a case from them. The files derived from that data (everything in `benchmark/`) are under the same CDLA-Sharing-1.0 licence; the code is MIT.

**Where things are.**

| path | what it holds |
|---|---|
| `run.py` | runs one system on the 32 cases and saves its answers |
| `report.py` | rebuilds every table above from `results/` |
| `probe.py` | asks a model about laundering patterns directly, with no account |
| `benchmark/` | the test: `golden.jsonl` (the expected answers), `cases/` (what the model sees), `keys/` (the answer keys) |
| `src/` | what the commands are made of: the model under test and its prompt (`system.py`, `variants/`), the rule baseline, the two scoring rules (`aml_graders.py`), the statistics, and the runner, a copy of evals-kit |
| `results/` | every saved answer, and the saved reasoning of the two method runs |
| `prep/` | rebuilds the data and the cases |
| `tests/` | 52 checks, no API call |
| `docs/` | the full report, the notebook, and the models' answers account by account |

### How this was built

I did some quick research on the field, wrote the question, selected cases and slices, set the scoring rule and
prompt, made predictions before each run, and interpreted the results. Claude (Claude Code) wrote the scripts based
on these inputs (including the case builder, graders, rule file, runner script, and model client), reviewed the
models' reasoning in `results/`, maintained records in `docs/NOTEBOOK.md`, and drafted the initial version of this memo
from my notes.
