"""Reward redemption for the Fernlocket loyalty programme.

PR #412: move redemption off the nightly batch onto a synchronous endpoint.
"""
import logging
import uuid

from .db import transaction
from .fulfillment import FulfillmentClient, FulfillmentError

log = logging.getLogger(__name__)

MAX_PER_ORDER = 10

SORT_COLUMNS = {
    "newest": "created_at DESC",
    "oldest": "created_at ASC",
    "points": "points_spent DESC",
}


class RedemptionError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def redeem(conn, fulfillment: FulfillmentClient, member_id: str, payload: dict) -> dict:
    """Spend a member's points on a reward and ship it.

    Called by POST /members/{member_id}/redemptions with the JSON body as `payload`.
    """
    reward_id = payload["reward_id"]
    quantity = int(payload.get("quantity", 1))
    if quantity > MAX_PER_ORDER:
        raise RedemptionError(400, f"at most {MAX_PER_ORDER} of a reward per order")

    with transaction(conn) as cur:
        cur.execute(
            "SELECT points_cost, active FROM rewards WHERE id = %s",
            (reward_id,),
        )
        row = cur.fetchone()
        if row is None or not row[1]:
            raise RedemptionError(404, "reward not available")
        cost = row[0] * quantity

        # Lock the member's balance row so two taps on "Redeem" can't both spend it.
        cur.execute(
            "SELECT balance FROM point_accounts WHERE member_id = %s FOR UPDATE",
            (member_id,),
        )
        balance = cur.fetchone()[0]
        if balance < cost:
            raise RedemptionError(409, "not enough points")

        redemption_id = str(uuid.uuid4())
        cur.execute(
            "UPDATE point_accounts SET balance = %s WHERE member_id = %s",
            (balance - cost, member_id),
        )
        cur.execute(
            "INSERT INTO redemptions (id, member_id, reward_id, quantity, points_spent, status)"
            " VALUES (%s, %s, %s, %s, %s, 'pending')",
            (redemption_id, member_id, reward_id, quantity, cost),
        )
    # transaction commits on leaving the block

    try:
        fulfillment.ship(redemption_id, reward_id, quantity)
    except FulfillmentError:
        log.exception("fulfillment failed for redemption %s", redemption_id)
        raise RedemptionError(502, "We couldn't send your reward. Please try again.")

    with transaction(conn) as cur:
        cur.execute(
            "UPDATE redemptions SET status = 'shipped' WHERE id = %s",
            (redemption_id,),
        )

    return {
        "redemption_id": redemption_id,
        "points_spent": cost,
        "balance": balance - cost,
    }


def list_redemptions(conn, member_id: str, sort: str = "newest", limit: int = 20) -> list:
    """Redemption history for the member's account screen."""
    order_by = SORT_COLUMNS.get(sort)
    if order_by is None:
        raise RedemptionError(400, "unknown sort")
    limit = max(1, min(int(limit), 100))

    with transaction(conn) as cur:
        cur.execute(
            "SELECT id, reward_id, quantity, points_spent, status, created_at"
            f" FROM redemptions WHERE member_id = %s ORDER BY {order_by} LIMIT %s",
            (member_id, limit),
        )
        return cur.fetchall()
