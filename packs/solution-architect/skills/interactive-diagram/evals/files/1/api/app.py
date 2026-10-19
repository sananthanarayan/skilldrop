import json
import os

import psycopg
import redis
from flask import Flask, jsonify, request

app = Flask(__name__)
db = psycopg.connect(os.environ["DATABASE_URL"])
queue = redis.Redis.from_url(os.environ["REDIS_URL"])


def validate(order):
    if not order.get("items"):
        return "an order needs at least one item"
    if not order.get("email"):
        return "an order needs an email for the confirmation"


@app.post("/orders")
def place_order():
    order = request.get_json()
    problem = validate(order)
    if problem:
        # the first rule the order breaks, in words the storefront can show
        return jsonify(error=problem), 400
    with db.cursor() as cur:
        cur.execute(
            "insert into orders (shop_id, email, items) values (%s, %s, %s) returning id",
            (order["shop_id"], order["email"], json.dumps(order["items"])),
        )
        order_id = cur.fetchone()[0]
    db.commit()
    queue.lpush("emails", json.dumps({"order_id": order_id, "to": order["email"]}))
    return jsonify(id=order_id), 201


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    with db.cursor() as cur:
        cur.execute("select id, status from orders where id = %s", (order_id,))
        row = cur.fetchone()
    return jsonify(id=row[0], status=row[1]) if row else ("", 404)
