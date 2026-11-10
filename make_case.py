"""Turn one account of IBM's synthetic bank into a case file and its answer key.

Boilerplate, written by Claude on Nov 7, 2026 (like fake_system.py in evals_kit): it only cuts and formats
data. The eval itself (the alert text, what the model is asked, the expected answer, the graders, the run)
is yours.

    python make_case.py attempts                  # the 370 laundering attempts, one line each
    python make_case.py attempts --type CYCLE     # only one pattern type
    python make_case.py normal                    # normal accounts with 10 to 60 transactions
    python make_case.py build P01 8000ABC12       # writes cases/P01.md and keys/P01.json
    python make_case.py blind 4                   # B01-B04: half laundering, shuffled, nothing printed about which

Reads data/aml/ (gitignored; how it was made: prep/README.md). Standard library only.
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data" / "aml"
TRANS = DATA / "kept_transactions.csv"
PATTERNS = DATA / "HI-Small_Patterns.txt"
NORMAL = DATA / "kept_transactions.csv.normal_accounts.txt"


def row_key(fields):
    # time, from bank, from account, to bank, to account, amount paid: unique enough to match a row
    return (fields[0], fields[1], fields[2], fields[3], fields[4], fields[7])


def load_attempts():
    """Each attempt: its number (1 to 370), pattern type, and the keys of its rows."""
    attempts, current = [], None
    for line in PATTERNS.read_text().splitlines():
        if line.startswith("BEGIN LAUNDERING ATTEMPT"):
            kind = line.split(" - ", 1)[1].split(":")[0].strip()
            current = {"n": len(attempts) + 1, "type": kind, "rows": []}
        elif line.startswith("END LAUNDERING ATTEMPT"):
            attempts.append(current)
            current = None
        elif current is not None and line.count(",") == 10:
            current["rows"].append(line.split(","))
    return attempts


def load_rows():
    with TRANS.open() as f:
        reader = csv.reader(f)
        next(reader)
        return [r for r in reader if len(r) == 11]


def cmd_attempts(only_type=None):
    for a in load_attempts():
        if only_type and a["type"] != only_type:
            continue
        accounts = Counter()
        for r in a["rows"]:
            accounts[r[2]] += 1
            accounts[r[4]] += 1
        main, hits = accounts.most_common(1)[0]
        days = sorted({r[0][:10] for r in a["rows"]})
        print(f"#{a['n']:>3}  {a['type']:<15} {len(a['rows']):>3} rows  {len(accounts):>3} accounts  "
              f"{days[0]} to {days[-1]}  busiest account {main} ({hits} rows)")


def clean_normal(lo=10, hi=60):
    normal = set(NORMAL.read_text().split())
    count, dirty = Counter(), set()
    for r in load_rows():
        for acct in (r[2], r[4]):
            if acct in normal:
                count[acct] += 1
                if r[10] == "1":
                    dirty.add(acct)  # touches a laundering row: never use it as a "close" case
    return sorted(a for a in normal if lo <= count[a] <= hi and a not in dirty), count, dirty


def cmd_normal(lo=10, hi=60):
    ok, count, dirty = clean_normal(lo, hi)
    print(f"{len(ok)} normal accounts with {lo} to {hi} transactions (accounts touching a laundering row "
          f"left out: {len(dirty)})")
    for a in ok:
        print(f"  {a}  {count[a]} transactions")


def cmd_blind(n):
    """Half laundering, half normal, shuffled, built as B01… so you can work them without knowing which is which."""
    import random
    rng = random.SystemRandom()
    busiest = []
    for a in load_attempts():
        accounts = Counter()
        for r in a["rows"]:
            accounts[r[2]] += 1
            accounts[r[4]] += 1
        busiest.append(accounts.most_common(1)[0][0])
    picks = rng.sample(busiest, n // 2) + rng.sample(clean_normal()[0], n - n // 2)
    rng.shuffle(picks)
    import contextlib, io
    for i, acct in enumerate(picks, 1):
        with contextlib.redirect_stdout(io.StringIO()):  # build's message would say how many laundering rows
            cmd_build(f"B{i:02d}", acct)
    print(f"cases/B01.md to B{n:02d}.md written, about half laundering, in random order. Work them as the "
          "analyst and write your answers down before opening keys/B*.json.")


def cmd_build(case_id, account):
    laundering = {}
    for a in load_attempts():
        for r in a["rows"]:
            laundering[row_key(r)] = (a["n"], a["type"])
    history = [r for r in load_rows() if account in (r[2], r[4])]
    if not history:
        sys.exit(f"no transactions for account {account}")
    history.sort(key=lambda r: r[0])

    lines = [f"# Account {account}", "",
             f"{len(history)} transactions, {history[0][0]} to {history[-1][0]}. "
             "Amounts as paid by the sender. 'out' = this account paid, 'in' = it received.", "",
             "| id | time | direction | counterparty (bank / account) | amount | currency | format |",
             "|---|---|---|---|---|---|---|"]
    key_rows, key_attempts, other_rows = [], set(), []
    for i, r in enumerate(history, 1):
        tid = f"T{i:03d}"
        if r[2] == r[4]:
            direction, other = "self", "-"
        elif r[2] == account:
            direction, other = "out", f"{r[3]} / {r[4]}"
        else:
            direction, other = "in", f"{r[1]} / {r[2]}"
        lines.append(f"| {tid} | {r[0]} | {direction} | {other} | {r[7]} | {r[8]} | {r[9]} |")
        hit = laundering.get(row_key(r))
        if hit:
            key_rows.append(tid)
            key_attempts.add(hit)
        elif r[10] == "1":
            other_rows.append(tid)  # labelled laundering but in no listed attempt (58 such rows in the data)

    (HERE / "cases").mkdir(exist_ok=True)
    (HERE / "keys").mkdir(exist_ok=True)
    (HERE / "cases" / f"{case_id}.md").write_text("\n".join(lines) + "\n")
    key = {"case": case_id, "account": account, "n_transactions": len(history),
           "laundering": bool(key_rows or other_rows), "laundering_rows": key_rows,
           "attempts": [{"n": n, "type": t} for n, t in sorted(key_attempts)],
           "labelled_rows_outside_attempts": other_rows}
    (HERE / "keys" / f"{case_id}.json").write_text(json.dumps(key, indent=2) + "\n")
    print(f"cases/{case_id}.md written ({len(history)} transactions); keys/{case_id}.json written "
          f"(laundering rows: {len(key_rows)}). Do not open the key until your expected answer is written.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["attempts"]:
        cmd_attempts(args[2] if args[1:2] == ["--type"] else None)
    elif args[:1] == ["normal"]:
        cmd_normal()
    elif args[:1] == ["blind"] and len(args) == 2:
        cmd_blind(int(args[1]))
    elif args[:1] == ["build"] and len(args) == 3:
        cmd_build(args[1], args[2])
    else:
        sys.exit(__doc__)
