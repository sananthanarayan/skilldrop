from decimal import Decimal
from typing import Iterator, List, Tuple

from .rules import Account

RECORD_LEN = 43


def parse_extract(lines) -> Tuple[List[Account], int]:
    """Parse the fixed-width extract. Returns (accounts, skipped_count)."""
    accounts: List[Account] = []
    skipped = 0
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        if len(line) != RECORD_LEN:
            skipped += 1
            continue
        try:
            pence = int(line[28:38])
            days = int(line[38:42])
        except ValueError:
            skipped += 1
            continue
        accounts.append(Account(
            account_id=line[0:8],
            name=line[8:28].strip(),
            balance=Decimal(pence) / 100,
            days_overdue=days,
            tier=line[42],
        ))
    return accounts, skipped
