from decimal import Decimal

VAT = {"EU": Decimal("0.21"), "UK": Decimal("0.20"), "US": Decimal("0.00")}


def vat(region: str, taxable: Decimal) -> Decimal:
    return (taxable * VAT[region]).quantize(Decimal("0.01"))
