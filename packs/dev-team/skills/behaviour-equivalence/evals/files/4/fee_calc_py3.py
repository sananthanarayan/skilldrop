# fee_calc.py -- Python 3.12 port
import csv
import sys
from datetime import datetime


def main(inp, outp):
    fees = {}
    with open(inp, newline="") as f:
        for row in csv.DictReader(f):
            fee = round(int(row["amount_cents"]) * int(row["rate_bp"]) / 10000)
            # no fee -> no currency needed downstream
            ccy = row["currency"] if fee > 0 else ""
            fees[row["account_id"]] = (fee, ccy)
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(outp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["account_id", "fee_cents", "currency", "run_ts"])
        for acct, (fee, ccy) in fees.items():
            w.writerow([acct, fee, ccy, ts])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
