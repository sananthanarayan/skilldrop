from datetime import date
from decimal import Decimal
from pathlib import Path
import csv

import pytest

from ledgerline.errors import ParseError
from ledgerline.parsers.acme import AcmeParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_sample_rows():
    rows = list(csv.reader(open(FIXTURES / "acme_sample.csv", encoding="utf-8")))
    entries = [AcmeParser(currency="GBP").parse_row(r) for r in rows[1:]]
    assert entries[0].on == date(2026, 3, 2)
    assert entries[1].amount == Decimal("-12.00")


def test_bad_date_names_the_column():
    with pytest.raises(ParseError, match="Date"):
        AcmeParser(currency="GBP").parse_row(["2026-03-02", "Cafe", "3.10", "0"])
