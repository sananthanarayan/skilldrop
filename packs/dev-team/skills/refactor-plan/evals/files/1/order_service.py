# orders/order_service.py  (Lantern Outfitters web shop, fictional)
# Excerpt: the full file is 1,812 lines. Signatures are complete; bodies shown only where
# they matter. Elided bodies are marked "...".

from decimal import Decimal, ROUND_HALF_UP

from orders.models import Order, OrderLine
from infra import stock_db          # direct DB client
from infra import payments_gateway  # third-party SDK wrapper
from infra import smtp_client       # sends mail synchronously
from finance.csv_writer import write_row


class OrderService:
    """Creates, prices, pays for, fulfils, cancels, refunds and exports orders."""

    def create_order(self, customer, cart, promo_code=None):
        order = Order(customer=customer)
        for item in cart.items:
            order.lines.append(OrderLine(sku=item.sku, qty=item.qty, unit_price=item.price))
        self.apply_discounts(order, promo_code)
        self.calculate_tax(order)
        self.reserve_stock(order)
        result = self.charge_payment(order)
        self.send_confirmation_email(order)   # sent even when result.ok is False
        order.status = "paid" if result.ok else "payment_failed"
        order.save()
        return order

    def apply_discounts(self, order, promo_code):
        for line in order.lines:
            if line.qty <= 0:
                # Returns flow builds negative-qty lines and relies on them pricing at zero.
                line.price = Decimal("0")
                continue
            line.price = line.unit_price * line.qty
        if promo_code:
            ...  # 140 lines: percentage, fixed-amount, buy-x-get-y, staff discount

    def calculate_tax(self, order):
        rate = Decimal("0.20")
        total_tax = Decimal("0")
        for line in order.lines:
            # Rounds per line, not per order. Invoices issued since 2021 depend on this.
            line_tax = (line.price * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            line.tax = line_tax
            total_tax += line_tax
        order.tax = total_tax

    def reserve_stock(self, order):
        for line in order.lines:
            stock_db.execute("UPDATE stock SET reserved = reserved + %s WHERE sku = %s",
                             (line.qty, line.sku))

    def charge_payment(self, order):
        ...  # 210 lines: retries, 3-D Secure, gateway error mapping
        return payments_gateway.charge(order.customer.payment_token, order.total())

    def send_confirmation_email(self, order):
        body = self._render_confirmation(order)
        smtp_client.send(to=order.customer.email, subject="Your order", body=body)

    def _render_confirmation(self, order):
        ...  # 180 lines of string templating

    def cancel_order(self, order):
        ...  # calls stock_db directly, then payments_gateway.void, then smtp_client.send

    def refund(self, order, lines):
        ...  # builds negative-qty lines, calls apply_discounts and calculate_tax, then
             # payments_gateway.refund and smtp_client.send

    def export_for_finance(self, orders, path):
        ...  # 260 lines: one CSV row per order line via finance.csv_writer.write_row
