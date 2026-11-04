from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

GRACE_DAYS = 14
RATES = {"S": Decimal("0.015"), "P": Decimal("0.010")}
MIN_FEE = Decimal("5.00")
CAPS = {"P": Decimal("25.00")}
SECOND_STAGE_DAYS = 90
PENNY = Decimal("0.01")


@dataclass(frozen=True)
class Account:
    account_id: str
    name: str
    balance: Decimal   # pounds
    days_overdue: int
    tier: str


def _cap(fee: Decimal, tier: str) -> Decimal:
    cap = CAPS.get(tier)
    return min(fee, cap) if cap is not None else fee


def late_fee(acct: Account) -> Decimal:
    """Return the late fee in pounds for one account (0 if none is due)."""
    if acct.days_overdue <= GRACE_DAYS:
        return Decimal("0")
    if acct.balance <= 0:
        # Nothing owed, so nothing to charge.
        return Decimal("0")
    tier = acct.tier if acct.tier in RATES else "S"
    fee = (acct.balance * RATES[tier]).quantize(PENNY, rounding=ROUND_HALF_EVEN)
    fee = max(fee, MIN_FEE)
    fee = _cap(fee, tier)
    if acct.days_overdue > SECOND_STAGE_DAYS:
        fee = _cap(fee * 2, tier)
    return fee
