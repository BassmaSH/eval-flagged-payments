# Where the data in `data/aml/` comes from

*Prepared by Claude on Nov 7, 2026, with Bassma's go-ahead for each download. `data/` is gitignored, so this
page is the only record of how to rebuild it.*

**Source.** IBM's synthetic anti-money-laundering data, split "HI-Small" (HI = higher share of laundering).
Paper: Altman et al., *Realistic Synthetic Financial Transactions for Anti-Money Laundering Models*, NeurIPS 2023
Datasets and Benchmarks, <https://arxiv.org/abs/2306.16424>. IBM's own copies are on Kaggle
(`ealtman2019/ibm-transactions-for-anti-money-laundering-aml`) and IBM Box; both need a login. The files here
come from the Hugging Face mirror `OsamaMIT/IBM-AML-HI-Small` (the same file size as two other mirrors,
475,664,283 bytes; the contents were not compared). Licence of the data: CDLA-Sharing-1.0. Everything is simulated: no real person or bank.

**What is in `data/aml/`.**

| file | size | what it is |
|---|---|---|
| `HI-Small_Patterns.txt` | 324 KB | the 370 laundering attempts, each between `BEGIN LAUNDERING ATTEMPT - <TYPE>` and `END …`, one transaction per line. **This is the label.** |
| `kept_transactions.csv` | 21 MB | every transaction (Sep 1–18, 2022) that touches one of 3,170 accounts in the attempts or 3,000 normal accounts sampled at random (seed 7). 223,212 rows out of 5,078,345. |
| `kept_transactions.csv.normal_accounts.txt` | 30 KB | the 3,000 sampled normal accounts |

**How it was made.** The full 476 MB file was streamed once through `filter_aml.py` and only the kept rows were
written to disk:

```bash
mkdir -p data/aml && cd data/aml
B=https://huggingface.co/datasets/OsamaMIT/IBM-AML-HI-Small/resolve/main
curl -sL -o HI-Small_Patterns.txt "$B/HI-Small_Patterns.txt"
curl -sL -r 0-41943039 -o first40MB.csv "$B/HI-Small_Trans.csv"   # only for drawing the normal accounts
curl -sL "$B/HI-Small_Trans.csv" | python3 -I ../../prep/filter_aml.py HI-Small_Patterns.txt first40MB.csv kept_transactions.csv
rm first40MB.csv
```

The normal accounts are drawn from the first 40 MB (Sep 1, 00:00 to 03:47), so they are accounts active on the
first morning; their full 18 days are then kept.

**Measured on the kept data.**
- Attempts by type: BIPARTITE 49 · CYCLE 54 · FAN-IN 40 · FAN-OUT 48 · GATHER-SCATTER 51 · RANDOM 41 ·
  SCATTER-GATHER 44 · STACK 43.
- Normal accounts: median 29 transactions over the 18 days, 90th percentile 98, maximum 260; 1,430 have
  between 10 and 60 transactions and touch no laundering row.
- 17 sampled "normal" accounts touch a laundering row. `make_case.py normal` leaves them out.
- 3,267 kept rows have `Is Laundering = 1`; 3,209 of them belong to a listed attempt. The other 58 are
  laundering by the column but in no attempt: `make_case.py` lists them separately in the key.
- The CSV's original header repeats `Account` twice; the kept file names them `From Account` and `To Account`.
