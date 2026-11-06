import argparse
import csv
import os
import sys

from ledgerline.detect import detect_bank
from ledgerline.errors import ParseError
from ledgerline.parsers import PARSERS


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ledgerline")
    ap.add_argument("statement")
    ap.add_argument("--bank", help="skip detection and use this parser")
    args = ap.parse_args(argv)
    currency = os.environ.get("LEDGERLINE_CURRENCY", "GBP")
    with open(args.statement, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    bank = args.bank or detect_bank(rows[0])
    parser = PARSERS[bank](currency=currency)
    writer = csv.writer(sys.stdout)
    for n, row in enumerate(rows[1:], start=2):
        try:
            writer.writerow(parser.parse_row(row).as_csv())
        except ParseError as e:
            print(f"line {n}: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
