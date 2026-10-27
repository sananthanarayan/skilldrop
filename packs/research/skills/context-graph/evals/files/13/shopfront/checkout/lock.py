"""Hold prices steady while a cart is in checkout (RFC-015)."""
from shopfront.pricing import cache

LOCK_SECONDS = 15 * 60


def lock_cart_prices(cart) -> None:
    for line in cart.lines:
        cache.get_price(line.sku)              # make sure the entry exists
        cache.touch(line.sku, LOCK_SECONDS)    # keep it alive for the checkout window


def price_for_charge(sku: str) -> dict:
    return cache.get_price(sku)
