from ledgerline.errors import ParseError

# Header row of each bank's export -> parser name in PARSERS.
HEADER_SIGNATURES = {
    ("Date", "Description", "Amount", "Balance"): "acme",
    ("Posted", "Payee", "Debit", "Credit"): "harbor",
}


def detect_bank(header):
    key = tuple(cell.strip() for cell in header)
    try:
        return HEADER_SIGNATURES[key]
    except KeyError:
        raise ParseError(f"unrecognised header {list(key)}; pass --bank")
