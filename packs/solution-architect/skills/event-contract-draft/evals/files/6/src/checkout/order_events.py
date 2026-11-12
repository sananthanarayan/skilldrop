"""Order events emitted by the Larkspur Goods checkout service.

Today these go onto the `orders` Kafka topic. Nobody wrote down a contract;
this module *is* the contract right now.
"""

import json
from datetime import datetime, timezone

from checkout.db import session
from checkout.kafka import producer  # configured in checkout/kafka.py with acks=1, enable.idempotence=false

TOPIC = "orders"


def _publish(event_type: str, order, extra: dict | None = None) -> None:
    body = {
        "event_type": event_type,
        "ts": datetime.now(timezone.utc).isoformat(),
        "order_id": order.id,
        "customer_id": order.customer_id,
        "customer_email": order.customer.email,
        "customer_phone": order.customer.phone,
        "shipping_address": order.shipping_address.as_dict(),
        "card_number": order.payment.card_number,
        "card_expiry": order.payment.card_expiry,
        "total": float(order.total),
        "currency": order.currency,
        "lines": [
            {"sku": line.sku, "qty": line.qty, "unit_price": float(line.unit_price)}
            for line in order.lines
        ],
        "status": order.status,
    }
    if extra:
        body.update(extra)
    # TODO: pick a key. Round-robin for now so partitions stay even.
    producer.send(TOPIC, key=None, value=json.dumps(body).encode())


def create_order(order) -> None:
    session.add(order)
    _publish("create_order", order)
    session.commit()


def update_order_status(order, new_status: str) -> None:
    # new_status is one of: "paid", "packed", "shipped", "delivered"
    order.status = new_status
    _publish("update_order_status", order, {"new_status": new_status})
    session.commit()


def cancel_order(order, reason: str) -> None:
    order.status = "cancelled"
    _publish("cancel_order", order, {"reason": reason})
    session.commit()
