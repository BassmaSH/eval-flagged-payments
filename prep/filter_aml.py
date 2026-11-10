import csv, random, sys
# Keep every row touching a laundering account (from Patterns) or one of ~3000 sampled normal accounts.
pat_accts = set()
for line in open(sys.argv[1]):
    p = line.strip().split(",")
    if len(p) == 11:
        pat_accts.add(p[2]); pat_accts.add(p[4])
random.seed(7)
slice_accts = set()
with open(sys.argv[2]) as f:
    r = csv.reader(f); next(r)
    for row in r:
        if len(row) == 11 and row[10] == "0" and row[2] != row[4]:
            slice_accts.add(row[2])
normal = set(random.sample(sorted(slice_accts - pat_accts), 3000))
keep = pat_accts | normal
out = csv.writer(open(sys.argv[3], "w", newline=""))
r = csv.reader(sys.stdin)
header = next(r)
out.writerow(["Timestamp","From Bank","From Account","To Bank","To Account","Amount Received","Receiving Currency","Amount Paid","Payment Currency","Payment Format","Is Laundering"])
n = k = 0
for row in r:
    n += 1
    if len(row) == 11 and (row[2] in keep or row[4] in keep):
        out.writerow(row); k += 1
open(sys.argv[3] + ".normal_accounts.txt", "w").write("\n".join(sorted(normal)))
print("rows read", n, "kept", k, "pattern accounts", len(pat_accts), "normal sampled", len(normal), file=sys.stderr)
