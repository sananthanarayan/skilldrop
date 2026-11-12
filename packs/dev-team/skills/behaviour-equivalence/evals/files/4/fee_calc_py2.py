# fee_calc.py -- Python 2.7, runs nightly on legacy box batch01
import csv, sys, datetime

def main(inp, outp):
    fees = {}
    for row in csv.DictReader(open(inp, 'rb')):
        fee = int(round(int(row['amount_cents']) * int(row['rate_bp']) / 10000.0))
        fees[row['account_id']] = (fee, row['currency'])
    ts = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    w = csv.writer(open(outp, 'wb'))
    w.writerow(['account_id', 'fee_cents', 'currency', 'run_ts'])
    for acct, (fee, ccy) in fees.items():
        w.writerow([acct, fee, ccy, ts])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
