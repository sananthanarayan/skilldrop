"""Fetch the current price for a SKU."""
import json
import urllib.request

from shopfront.settings import PRICING_SVC_URL


def fetch_price(sku: str) -> dict:
    with urllib.request.urlopen(f"{PRICING_SVC_URL}/v1/prices/{sku}", timeout=2) as resp:
        return json.load(resp)  # {"sku": ..., "amount_minor": ..., "currency": ...}
