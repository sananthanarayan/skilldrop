"""POST /checkout: price the cart, take payment, record the order, hand off fulfilment."""
import json
import os

import pika
import psycopg
import redis
import stripe
from fastapi import FastAPI, HTTPException

app = FastAPI()
db = psycopg.connect(os.environ["DATABASE_URL"])
prices = redis.Redis.from_url(os.environ["REDIS_URL"])
broker = pika.BlockingConnection(pika.URLParameters(os.environ["BROKER_URL"])).channel()


def price_cart(cart):
    total = 0
    for line in cart["lines"]:
        cached = prices.get(f"price:{line['sku']}")
        if cached is None:
            row = db.execute("select price from products where sku = %s", (line["sku"],)).fetchone()
            cached = row[0]
            prices.set(f"price:{line['sku']}", cached, ex=300)
        total += int(cached) * line["qty"]
    return total


@app.post("/checkout")
def checkout(cart: dict):
    total = price_cart(cart)
    intent = stripe.PaymentIntent.create(amount=total, currency="gbp", confirm=True,
                                         payment_method=cart["payment_method"])
    if intent.status != "succeeded":
        raise HTTPException(402, "payment declined")
    order_id = db.execute("insert into orders (email, total, payment_id) values (%s, %s, %s) returning id",
                          (cart["email"], total, intent.id)).fetchone()[0]
    db.commit()
    broker.basic_publish(exchange="", routing_key="fulfilment",
                         body=json.dumps({"order_id": order_id}))
    return {"order_id": order_id}
