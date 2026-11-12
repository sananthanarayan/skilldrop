from decimal import Decimal

PLACES = Decimal("0.0001")


class Amount:
    def __init__(self, value, currency):
        self.value = Decimal(value).quantize(PLACES)
        self.currency = currency
