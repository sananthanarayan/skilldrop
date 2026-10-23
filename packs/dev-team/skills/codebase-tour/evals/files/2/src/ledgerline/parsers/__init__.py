from ledgerline.parsers.acme import AcmeParser
from ledgerline.parsers.harbor import HarborParser

# Explicit registry: a parser module is not used until it is listed here.
PARSERS = {
    "acme": AcmeParser,
    "harbor": HarborParser,
}
