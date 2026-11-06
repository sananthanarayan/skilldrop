"""Consumes domain events and turns them into notifications."""
from kafka import KafkaConsumer

from services.notifications.dispatch import dispatch

TOPICS = ("user-events", "invoice-events")


def run(bootstrap_servers):
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=bootstrap_servers,
        group_id="notifications",
        enable_auto_commit=False,
    )
    for message in consumer:
        dispatch(message.topic, message.value)
        consumer.commit()
