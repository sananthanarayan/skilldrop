import json
import os

import redis
import requests

queue = redis.Redis.from_url(os.environ["REDIS_URL"])
MAILER_URL = os.environ["MAILER_URL"]


def run():
    while True:
        _, raw = queue.brpop("emails")
        job = json.loads(raw)
        requests.post(MAILER_URL, json={
            "to": job["to"],
            "template": "order-confirmation",
            "data": {"order_id": job["order_id"]},
        }, timeout=10)


if __name__ == "__main__":
    run()
