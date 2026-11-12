from decimal import Decimal

import pytest

from shipcalc.tax import vat


@pytest.mark.parametrize(
    "region,taxable,expected",
    [("EU", Decimal("100.00"), Decimal("21.00")), ("UK", Decimal("100.00"), Decimal("20.00")), ("US", Decimal("100.00"), Decimal("0.00"))],
)
def test_vat_by_region(region, taxable, expected):
    assert vat(region, taxable) == expected
