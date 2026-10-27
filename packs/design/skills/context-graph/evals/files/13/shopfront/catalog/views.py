"""Product detail page."""
from shopfront.pricing import cache


def product_detail(request, sku):
    product = request.catalog.get(sku)
    price = cache.get_price(sku)
    return request.render("product.html", {"product": product, "price": price})
