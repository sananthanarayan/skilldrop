from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Entry:
    id: str
    account_id: str
    amount_minor: int
    currency: str
    posted_at: datetime
    fx_amount: Optional[Decimal] = None
    fx_currency: Optional[str] = None
    fx_rate: Optional[Decimal] = None
