#!/usr/bin/env python3
# feecalc.py - nightly late-fee batch for Hartwell Water accounts
# Original: R. Penhallow, 2009. Ported from the old Perl job, "minimal changes".
# Reads the fixed-width account extract, writes the fee file for the billing upload.
#
# usage: python3 feecalc.py ACCOUNTS_FILE [RUN_DATE]
#   RUN_DATE is YYYYMMDD; defaults to today.
#
# Record layout (fixed width, 43 chars):
#   0-8    account id      (8, digits)
#   8-28   account name    (20, space padded)
#   28-38  balance pence   (10, signed, right aligned, e.g. "     12345" or "    -2000")
#   38-42  days overdue    (4, right aligned)
#   42     tier            (1: S = standard, P = priority/vulnerable customer)

import sys, time

GRACE = 14          # days before any fee applies
RATE = {'S': 150, 'P': 100}   # basis points of balance
MINFEE = 500        # pence
CAP = {'P': 2500}   # priority customers capped at 25.00
skipped = 0
total = 0
out = []

def fee_for(bal, days, tier):
    global total
    if days <= GRACE:
        return 0
    f = (bal * RATE[tier] + 5000) // 10000
    if f < MINFEE:
        f = MINFEE
    if tier in CAP and f > CAP[tier]:
        f = CAP[tier]
    if days > 90:
        f = f * 2     # second-stage arrears fee, per 2011 tariff
        if tier in CAP and f > CAP[tier]:
            f = CAP[tier]
    total = total + f
    return f

def main():
    global skipped
    if len(sys.argv) < 2:
        print("usage: feecalc.py ACCOUNTS_FILE [RUN_DATE]")
        sys.exit(2)
    run_date = sys.argv[2] if len(sys.argv) > 2 else time.strftime('%Y%m%d')
    for line in open(sys.argv[1]):
        line = line.rstrip('\n')
        if line.strip() == '' or line.startswith('#'):
            continue
        if len(line) != 43:
            skipped = skipped + 1
            continue
        acct = line[0:8]
        name = line[8:28].strip()
        try:
            bal = int(line[28:38])
            days = int(line[38:42])
        except ValueError:
            skipped = skipped + 1
            continue
        tier = line[42]
        if tier not in RATE:
            tier = 'S'
        f = fee_for(bal, days, tier)
        if f > 0:
            out.append('%s,%s,%d,%d.%02d' % (acct, name.upper(), days, f // 100, f % 100))
    print('# FEERUN %s generated %s' % (run_date, time.strftime('%Y-%m-%dT%H:%M:%S')))
    for o in out:
        print(o)
    print('# TOTAL %d.%02d RECORDS %d SKIPPED %d' % (total // 100, total % 100, len(out), skipped))

main()
