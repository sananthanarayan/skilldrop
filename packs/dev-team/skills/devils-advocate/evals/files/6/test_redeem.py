import pytest

from rewards.fulfillment import FulfillmentError
from rewards.redeem import RedemptionError, list_redemptions, redeem
from tests.fakes import FakeFulfillment, make_db


@pytest.fixture
def db():
    conn = make_db()
    conn.seed_member("m-100", balance=500)
    conn.seed_reward("r-mug", points_cost=120, active=True)
    conn.seed_reward("r-old-tote", points_cost=50, active=False)
    return conn


def test_happy_path(db):
    result = redeem(db, FakeFulfillment(), "m-100", {"reward_id": "r-mug", "quantity": 2})
    assert result["points_spent"] == 240
    assert db.balance("m-100") == 260


def test_not_enough_points(db):
    with pytest.raises(RedemptionError) as err:
        redeem(db, FakeFulfillment(), "m-100", {"reward_id": "r-mug", "quantity": 5})
    assert err.value.status == 409
    assert db.balance("m-100") == 500


def test_inactive_reward(db):
    with pytest.raises(RedemptionError) as err:
        redeem(db, FakeFulfillment(), "m-100", {"reward_id": "r-old-tote"})
    assert err.value.status == 404


def test_quantity_limit(db):
    with pytest.raises(RedemptionError) as err:
        redeem(db, FakeFulfillment(), "m-100", {"reward_id": "r-mug", "quantity": 11})
    assert err.value.status == 400


def test_fulfillment_failure_returns_502(db):
    """Regression for #398: a failed shipment must not cost the member their points."""
    fulfillment = FakeFulfillment(fail_with=FulfillmentError("carrier timeout"))
    with pytest.raises(RedemptionError) as err:
        redeem(db, fulfillment, "m-100", {"reward_id": "r-mug", "quantity": 1})
    assert err.value.status == 502
    assert fulfillment.calls == 1


def test_history_rejects_unknown_sort(db):
    with pytest.raises(RedemptionError) as err:
        list_redemptions(db, "m-100", sort="points; DROP TABLE redemptions")
    assert err.value.status == 400
