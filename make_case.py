"""Turn one account of IBM's synthetic bank into a case file and its answer key.

    python make_case.py attempts                  # the 370 laundering attempts, one line each
    python make_case.py attempts --type CYCLE     # only one pattern type
    python make_case.py normal                    # normal accounts with 10 to 60 transactions
    python make_case.py build P01 8000ABC12       # writes cases/P01.md and keys/P01.json
    python make_case.py blind 4                   # B01-B04: half laundering, shuffled, nothing printed about which

Reads data/aml/ (gitignored; how it was made: prep/README.md). Standard library only.

Written by Claude on Nov 7, 2026, reorganised on Nov 15: it only cuts and formats data. The eval itself (the
alert text, what the model is asked, the expected answer, the graders, the run) is the author's.
"""
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data" / "aml"
TRANS = DATA / "kept_transactions.csv"
PATTERNS = DATA / "HI-Small_Patterns.txt"
NORMAL = DATA / "kept_transactions.csv.normal_accounts.txt"

# The columns of a transaction, in IBM's order. A row is a list of 11 strings.
(TIME, FROM_BANK, FROM_ACCOUNT, TO_BANK, TO_ACCOUNT, AMOUNT_RECEIVED, RECEIVING_CURRENCY, AMOUNT_PAID,
 PAYMENT_CURRENCY, PAYMENT_FORMAT, IS_LAUNDERING) = range(11)
N_COLUMNS = 11

Row = list[str]


def row_key(row: Row) -> tuple[str, ...]:
    """What identifies a transaction in both files: time, the two bank/account pairs and the amount paid."""
    return (row[TIME], row[FROM_BANK], row[FROM_ACCOUNT], row[TO_BANK], row[TO_ACCOUNT], row[AMOUNT_PAID])


def load_attempts() -> list[dict]:
    """The laundering attempts listed in IBM's pattern file.

    Returns:
        One dict per attempt: "n" (1 to 370, its position in the file), "type" (for example "CYCLE") and "rows".
    """
    attempts, current = [], None
    for line in PATTERNS.read_text().splitlines():
        if line.startswith("BEGIN LAUNDERING ATTEMPT"):
            kind = line.split(" - ", 1)[1].split(":")[0].strip()
            current = {"n": len(attempts) + 1, "type": kind, "rows": []}
        elif line.startswith("END LAUNDERING ATTEMPT"):
            attempts.append(current)
            current = None
        elif current is not None and line.count(",") == N_COLUMNS - 1:
            current["rows"].append(line.split(","))
    return attempts


def load_rows() -> list[Row]:
    """Every kept transaction, without the header line."""
    with TRANS.open() as f:
        reader = csv.reader(f)
        next(reader)
        return [row for row in reader if len(row) == N_COLUMNS]


def accounts_in(attempt: dict) -> Counter:
    """account -> the number of times it appears in the attempt's rows, as sender or receiver."""
    accounts = Counter()
    for row in attempt["rows"]:
        accounts[row[FROM_ACCOUNT]] += 1
        accounts[row[TO_ACCOUNT]] += 1
    return accounts


def clean_normal(rows: list[Row], lo: int = 10, hi: int = 60) -> tuple[list[str], Counter, set[str]]:
    """The sampled normal accounts that can serve as a "close" case.

    Returns:
        The accounts with lo to hi transactions that touch no laundering row; the transaction count of every
        sampled account; and the sampled accounts that do touch a laundering row.
    """
    normal = set(NORMAL.read_text().split())
    count, dirty = Counter(), set()
    for row in rows:
        for account in (row[FROM_ACCOUNT], row[TO_ACCOUNT]):
            if account in normal:
                count[account] += 1
                if row[IS_LAUNDERING] == "1":
                    dirty.add(account)
    return sorted(a for a in normal if lo <= count[a] <= hi and a not in dirty), count, dirty


def build_case(case_id: str, account: str, attempts: list[dict], rows: list[Row]) -> tuple[str, dict]:
    """One account's transactions as the model sees them, and the answer key. Writes nothing.

    Returns:
        The text of cases/<case_id>.md and the content of keys/<case_id>.json.
    """
    laundering = {row_key(row): (a["n"], a["type"]) for a in attempts for row in a["rows"]}
    history = sorted((row for row in rows if account in (row[FROM_ACCOUNT], row[TO_ACCOUNT])),
                     key=lambda row: row[TIME])
    if not history:
        sys.exit(f"no transactions for account {account}")

    lines = [f"# Account {account}", "",
             f"{len(history)} transactions, {history[0][TIME]} to {history[-1][TIME]}. "
             "Amounts as paid by the sender. 'out' = this account paid, 'in' = it received.", "",
             "| id | time | direction | counterparty (bank / account) | amount | currency | format |",
             "|---|---|---|---|---|---|---|"]
    key_rows, key_attempts, other_rows = [], set(), []
    for i, row in enumerate(history, 1):
        row_id = f"T{i:03d}"
        if row[FROM_ACCOUNT] == row[TO_ACCOUNT]:
            direction, counterparty = "self", "-"
        elif row[FROM_ACCOUNT] == account:
            direction, counterparty = "out", f"{row[TO_BANK]} / {row[TO_ACCOUNT]}"
        else:
            direction, counterparty = "in", f"{row[FROM_BANK]} / {row[FROM_ACCOUNT]}"
        lines.append(f"| {row_id} | {row[TIME]} | {direction} | {counterparty} | {row[AMOUNT_PAID]} | "
                     f"{row[PAYMENT_CURRENCY]} | {row[PAYMENT_FORMAT]} |")
        attempt = laundering.get(row_key(row))
        if attempt:
            key_rows.append(row_id)
            key_attempts.add(attempt)
        elif row[IS_LAUNDERING] == "1":
            other_rows.append(row_id)  # labelled laundering but in no listed attempt (58 such rows in the data)

    key = {"case": case_id, "account": account, "n_transactions": len(history),
           "laundering": bool(key_rows or other_rows), "laundering_rows": key_rows,
           "attempts": [{"n": n, "type": kind} for n, kind in sorted(key_attempts)],
           "labelled_rows_outside_attempts": other_rows}
    return "\n".join(lines) + "\n", key


def write_case(case_id: str, text: str, key: dict) -> None:
    for folder in ("cases", "keys"):
        (HERE / folder).mkdir(exist_ok=True)
    (HERE / "cases" / f"{case_id}.md").write_text(text)
    (HERE / "keys" / f"{case_id}.json").write_text(json.dumps(key, indent=2) + "\n")


def cmd_attempts(args: list[str]) -> None:
    only_type = args[1] if args[:1] == ["--type"] and len(args) == 2 else None
    for attempt in load_attempts():
        if only_type and attempt["type"] != only_type:
            continue
        accounts = accounts_in(attempt)
        busiest, hits = accounts.most_common(1)[0]
        days = sorted({row[TIME][:10] for row in attempt["rows"]})
        print(f"#{attempt['n']:>3}  {attempt['type']:<15} {len(attempt['rows']):>3} rows  "
              f"{len(accounts):>3} accounts  {days[0]} to {days[-1]}  busiest account {busiest} ({hits} rows)")


def cmd_normal(args: list[str]) -> None:
    lo, hi = 10, 60
    usable, count, dirty = clean_normal(load_rows(), lo, hi)
    print(f"{len(usable)} normal accounts with {lo} to {hi} transactions (accounts touching a laundering row "
          f"left out: {len(dirty)})")
    for account in usable:
        print(f"  {account}  {count[account]} transactions")


def cmd_build(args: list[str]) -> None:
    case_id, account = args
    text, key = build_case(case_id, account, load_attempts(), load_rows())
    write_case(case_id, text, key)
    print(f"cases/{case_id}.md written ({key['n_transactions']} transactions); keys/{case_id}.json written "
          f"(laundering rows: {len(key['laundering_rows'])}). Do not open the key until your expected answer "
          "is written.")


def cmd_blind(args: list[str]) -> None:
    """Half laundering, half normal, shuffled, built as B01… to work them without knowing which is which."""
    n = int(args[0])
    attempts, rows = load_attempts(), load_rows()
    rng = random.SystemRandom()  # not seeded on purpose: nobody can know the draw in advance
    busiest = [accounts_in(attempt).most_common(1)[0][0] for attempt in attempts]
    picks = rng.sample(busiest, n // 2) + rng.sample(clean_normal(rows)[0], n - n // 2)
    rng.shuffle(picks)
    for i, account in enumerate(picks, 1):
        case_id = f"B{i:02d}"
        write_case(case_id, *build_case(case_id, account, attempts, rows))  # silent: no count of laundering rows
    print(f"cases/B01.md to B{n:02d}.md written, about half laundering, in random order. Work them as the "
          "analyst and write your answers down before opening keys/B*.json.")


# command -> (function, the numbers of arguments it accepts)
COMMANDS = {"attempts": (cmd_attempts, (0, 2)), "normal": (cmd_normal, (0,)),
            "build": (cmd_build, (2,)), "blind": (cmd_blind, (1,))}


def main(argv: list[str]) -> None:
    command, args = (argv[0], argv[1:]) if argv else ("", [])
    if command not in COMMANDS or len(args) not in COMMANDS[command][1]:
        sys.exit(__doc__)
    COMMANDS[command][0](args)


if __name__ == "__main__":
    main(sys.argv[1:])
