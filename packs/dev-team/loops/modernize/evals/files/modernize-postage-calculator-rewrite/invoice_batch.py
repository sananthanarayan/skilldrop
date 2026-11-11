"""Nightly batch: adds postage to each order line. Depends on postage.calc."""
import csv
import sys

import postage


def run(path):
    total = 0
    bad = 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            p = postage.calc(row["weight_g"], row["zone"])
            if p == -1:
                bad += 1
                continue
            total += p
    print(f"postage_total_pence={total} bad_rows={bad}")


if __name__ == "__main__":
    run(sys.argv[1])
