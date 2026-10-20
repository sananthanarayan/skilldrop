from billing.payments import charge_card, PaymentDeclined
import pytest


def test_charge_card_success(fake_gateway):
    fake_gateway.next_response = {"status": "ok", "id": "ch_1"}
    assert charge_card("cus_1", 1000, "GBP")["id"] == "ch_1"


def test_charge_card_declined(fake_gateway):
    fake_gateway.next_response = {"status": "declined"}
    with pytest.raises(PaymentDeclined):
        charge_card("cus_1", 1000, "GBP")
