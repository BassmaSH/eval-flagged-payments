"""Keep the rows of IBM's transaction file that touch a laundering account or a sampled normal one.

    curl -sL "$B/HI-Small_Trans.csv" | python3 filter_aml.py PATTERNS FIRST_40MB KEPT

Reads the full file on standard input, so the 476 MB never has to be stored. Writes KEPT and
KEPT.normal_accounts.txt. The steps around it are in prep/README.md.

Written by Claude on Nov 7, 2026, reorganised on Nov 15. Standard library only.
"""

import csv
import random
import sys

N_COLUMNS = 11
FROM_ACCOUNT, TO_ACCOUNT, IS_LAUNDERING = 2, 4, 10  # positions in IBM's columns
N_NORMAL = 3000  # normal accounts to sample
SEED = 7
# IBM's header names both account columns "Account"; the kept file tells them apart.
HEADER = [
    "Timestamp", "From Bank", "From Account", "To Bank", "To Account", "Amount Received",
    "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format", "Is Laundering",
]  # fmt: skip


def laundering_accounts(patterns_file: str) -> set[str]:
    """Returns every account that appears in a row of a laundering attempt."""
    accounts = set()
    with open(patterns_file) as f:
        for line in f:
            row = line.strip().split(",")
            if len(row) == N_COLUMNS:
                accounts.update((row[FROM_ACCOUNT], row[TO_ACCOUNT]))
    return accounts


def sample_normal_accounts(first_rows_file: str, exclude: set[str]) -> set[str]:
    """Returns N_NORMAL senders of a normal payment in the first rows, none of them in exclude."""
    senders = set()
    with open(first_rows_file) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            is_normal_payment = len(row) == N_COLUMNS and row[IS_LAUNDERING] == "0"
            if is_normal_payment and row[FROM_ACCOUNT] != row[TO_ACCOUNT]:
                senders.add(row[FROM_ACCOUNT])
    random.seed(SEED)
    return set(random.sample(sorted(senders - exclude), N_NORMAL))


def main(patterns_file: str, first_rows_file: str, kept_file: str) -> None:
    """Streams standard input to kept_file, keeping the rows that touch a chosen account."""
    laundering = laundering_accounts(patterns_file)
    normal = sample_normal_accounts(first_rows_file, exclude=laundering)
    keep = laundering | normal

    n_read = n_kept = 0
    with open(kept_file, "w", newline="") as out_file:
        out = csv.writer(out_file)
        out.writerow(HEADER)
        reader = csv.reader(sys.stdin)
        next(reader)
        for row in reader:
            n_read += 1
            if len(row) == N_COLUMNS and (row[FROM_ACCOUNT] in keep or row[TO_ACCOUNT] in keep):
                out.writerow(row)
                n_kept += 1
    with open(kept_file + ".normal_accounts.txt", "w") as f:
        f.write("\n".join(sorted(normal)))
    print(
        f"rows read {n_read} kept {n_kept} pattern accounts {len(laundering)} "
        f"normal sampled {len(normal)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
