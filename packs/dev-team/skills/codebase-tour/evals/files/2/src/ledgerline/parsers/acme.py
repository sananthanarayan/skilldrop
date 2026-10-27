from datetime import datetime

from ledgerline.errors import ParseError
from ledgerline.money import parse_amount
from ledgerline.parsers.base import BaseParser, Entry


class AcmeParser(BaseParser):
    date_format = "%d/%m/%Y"

    def parse_row(self, row):
        if len(row) != 4:
            raise ParseError(f"expected 4 columns, got {len(row)}")
        try:
            on = datetime.strptime(row[0], self.date_format).date()
        except ValueError:
            raise ParseError(f"Date {row[0]!r} is not DD/MM/YYYY")
        return Entry(on=on, payee=row[1].strip(), amount=parse_amount(row[2]), currency=self.currency)
