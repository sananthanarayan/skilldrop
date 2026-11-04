"""usage: python3 -m hartwell_fees.cli ACCOUNTS_FILE [RUN_DATE]"""
import sys
from datetime import datetime
from decimal import Decimal

from .extract import parse_extract
from .rules import late_fee


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    run_date = argv[1] if len(argv) > 1 else datetime.now().strftime("%Y%m%d")
    with open(argv[0]) as fh:
        accounts, skipped = parse_extract(fh)
    lines = []
    total = Decimal("0")
    for acct in accounts:
        fee = late_fee(acct)
        if fee > 0:
            total += fee
            lines.append(f"{acct.account_id},{acct.name.upper()},{acct.days_overdue},{fee:.2f}")
    print(f"# FEERUN {run_date} generated {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    for line in lines:
        print(line)
    print(f"# TOTAL {total:.2f} RECORDS {len(lines)} SKIPPED {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
