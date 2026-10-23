from datetime import datetime
from decimal import Decimal

from ledgerline.parsers.base import BaseParser, Entry


class HarborParser(BaseParser):
    def parse_row(self, row):
        on = datetime.strptime(row[0], self.date_format).date()
        # Harbor splits debit and credit into two columns.
        debit = Decimal(row[2].replace(",", "") or "0")
        credit = Decimal(row[3].replace(",", "") or "0")
        return Entry(on=on, payee=row[1].strip(), amount=credit - debit, currency=self.currency)
