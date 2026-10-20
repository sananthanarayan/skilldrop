import pytest

from ledgerline.detect import detect_bank
from ledgerline.errors import ParseError


def test_detects_acme_header():
    assert detect_bank(["Date", "Description", "Amount", "Balance"]) == "acme"


def test_unknown_header_tells_the_user_to_pass_bank():
    with pytest.raises(ParseError, match="--bank"):
        detect_bank(["When", "What", "How much"])
