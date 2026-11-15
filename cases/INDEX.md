# Cases (Nov 7, 2026)

*Bassma's words, as she wrote them in the session.*

## Choices

- **Ratio:** 16 laundering (escalate) against 8 normal (close). A model that always answers escalate gets 66% right
  overall: that is the floor. Sliced by decision it gets 100% on the escalate slice and 0% on the close slice.
  More normal accounts to be added: with 8, each close case is 12.5 points on the slice that carries the value.
- **Hub accounts** (in many attempts: P05, P07, P09, P11, P14, P16) **and cases over 100 rows** (P05, P06, P07):
  kept. "I don't see why I would drop important examples." Reported as a **separate slice**.
- **Decision and evidence:** two golden lines per case, `<id>-decision` and `<id>-rows`; `system.py` caches the
  answer per input so both lines grade the same call.
- **Evidence pass rule (written before any run):** more than half of the laundering rows cited, and no normal row
  cited. Normal accounts get a rows line too: the right answer is an empty list ("it's also to see what tripped the
  model"). Needs a new grader (`contains_none` passes an empty answer; "more than half" is not expressible).
- **Ratio, revised:** half normal: 16 laundering, 16 normal (8 more normal accounts to add, P25–P32).

## The cases

| case | account | what it is | her judgement |
|---|---|---|---|
| P01 | 8013C4030 | CYCLE | easy, there are only two rows that stand out |
| P02 | 80F2C2FA0 | CYCLE | same as P01 |
| P03 | 803B24460 | FAN-OUT | easy, multiple outs to different accounts in different currencies |
| P04 | 80E5157A0 | FAN-OUT | hard, not a lot of transactions |
| P05 | 811B83280 | FAN-IN pick | hard, but it's flagged as multiple things in the key? |
| P06 | 8001D5B50 | FAN-IN | hard, because I assumed scatter-gather; I don't understand why some rows are not flagged |
| P07 | 80266F880 | GATHER-SCATTER pick | |
| P08 | 80154AAF0 | GATHER-SCATTER | |
| P09 | 812A09D40 | SCATTER-GATHER pick | |
| P10 | 80B1BF360 | SCATTER-GATHER | |
| P11 | 812D127D0 | BIPARTITE pick | |
| P12 | 811B6E2B0 | BIPARTITE pick | |
| P13 | 80963CB30 | STACK | |
| P14 | 812D0C600 | STACK pick | |
| P15 | 808946C20 | RANDOM | |
| P16 | 811FFF630 | RANDOM pick | |
| P17 | 80C7DE800 | normal | |
| P18 | 805208500 | normal | |
| P19 | 8086C3910 | normal | |
| P20 | 80D6EA9F0 | normal | |
| P21 | 8136E1601 | normal | |
| P22 | 80814F840 | normal | |
| P23 | 804AF7240 | normal | |
| P24 | 80319DA20 | normal | |
| P25 | 806E30F00 | normal, picked to look suspicious | 57 out to 10 accounts, one payment of 354 million |
| P26 | 80CED1670 | normal, picked to look suspicious | 34 in from 2 accounts, 20 out to 1 |
| P27 | 800784F10 | normal, picked to look suspicious | 46 out to 5 accounts, largest 15.7 million |
| P28 | 801408060 | normal, picked to look suspicious | 35 out to 6 accounts, 5 formats |
| P29 | 80EAA7180 | normal, picked to look suspicious | 29 out, 27 in, largest 838 thousand |
| P30 | 8007F4680 | normal, picked to look suspicious | 57 out to 4 accounts, nothing in |
| P31 | 802545DC0 | normal, picked to look suspicious | 55 out to 3 accounts, nothing in, largest 7.2 million |
| P32 | 80F022480 | normal, picked to look suspicious | 42 out to 5 accounts, 5 formats |

P17–P24 were picked at random from the normal list; P25–P32 were picked from 15 candidates with `prep/peek.py`
because they look most like an alert.

## Who wrote what

- `prep/make_golden.py`: written by Claude on Nov 8 at her request ("I can write the code on the next eval"), from her
  choices above. It writes `golden.jsonl`: 64 lines, slices `decision-` and `rows-` × `escalate-single` (10),
  `escalate-hub` (6), `close` (16). Input is the case path, `cases/P01.md`.
- `aml_graders.py`, `system.py`, `rule.py`, `run.py`: written by Claude on Nov 8 at her request ("write and I
  review line by line"), from her choices. `prep/peek.py`: Claude's screening helper.

## Where she stopped

All three runs done (Nov 8), no infra_error, answers in `results/`:

| slice | n | rule | small | large |
|---|---|---|---|---|
| decision-escalate-single | 10 | 30.0% | 100.0% | 100.0% |
| rows-escalate-single | 10 | 10.0% | 0.0% | 10.0% |
| decision-escalate-hub | 6 | 16.7% | 100.0% | 100.0% |
| rows-escalate-hub | 6 | 0.0% | 0.0% | 0.0% |
| decision-close | 16 | 93.8% | 0.0% | 0.0% |
| rows-close | 16 | 93.8% | 0.0% | 0.0% |

`MEMO.md` drafted by Claude from her notes, at her request ("draft it, I'll edit").

Then three prompt variants on all 32 cases, both models (Nov 8; `variants/`, answers in
`results/<model>+<variant>.json`, predictions and reasons in `docs/NOTEBOOK.md`): `simulated`, `objective`, `both`.
None met the bar written before the last run. Large escalated everything in every run; Small with both sentences
closed 69% of normal accounts and 63% of laundering ones; evidence never rose. Then `mistral-large-4` (same as the others: escalated
all 32) and `claude-opus-5-5` as an outside reference (one run, no temperature setting: close 88%, escalate 80% /
50%, evidence 20% / 17%). Memo rewritten around the gap between them, with her reading.
Nov 9: harness check on Large 4, Claude's schema at temperature 0, then at temperature 1: unchanged (0% close). She
stopped here. Open: Claude reruns (no credits), her edit of the memo, publish prep. Next: her edit of the memo; then, if she wants it, the folder made ready to publish.
