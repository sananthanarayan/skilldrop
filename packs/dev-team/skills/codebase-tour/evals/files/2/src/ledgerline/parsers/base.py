from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Entry:
    on: date
    payee: str
    amount: Decimal
    currency: str

    def as_csv(self):
        return [self.on.isoformat(), self.payee, f"{self.amount:.2f}", self.currency]


class BaseParser:
    date_format = "%Y-%m-%d"

    def __init__(self, currency: str):
        self.currency = currency

    def parse_row(self, row) -> Entry:
        raise NotImplementedError
