"""Phase 1 of the event store rollout: append every charge as an event."""

EVENTS_TABLE = "billing-events"


def append_charge_event(client, invoice_id, amount_minor, at):
    client.put_item(
        TableName=EVENTS_TABLE,
        Item={"invoice_id": invoice_id, "type": "charge", "amount_minor": amount_minor, "at": at},
    )
