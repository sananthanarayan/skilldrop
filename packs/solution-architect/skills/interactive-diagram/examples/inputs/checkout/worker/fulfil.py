"""Consumes the fulfilment queue and books a courier for each paid order."""
import json
import os

import pika
import psycopg
import requests

db = psycopg.connect(os.environ["DATABASE_URL"])
channel = pika.BlockingConnection(pika.URLParameters(os.environ["BROKER_URL"])).channel()


def on_message(ch, method, properties, body):
    order_id = json.loads(body)["order_id"]
    address = db.execute("select address from orders where id = %s", (order_id,)).fetchone()[0]
    booking = requests.post("https://courier.example/v2/bookings", json={"ref": order_id, "to": address}, timeout=10)
    db.execute("update orders set status = 'booked', courier_ref = %s where id = %s", (booking.json()["ref"], order_id))
    db.commit()
    ch.basic_ack(method.delivery_tag)


channel.basic_consume(queue="fulfilment", on_message_callback=on_message)
channel.start_consuming()
