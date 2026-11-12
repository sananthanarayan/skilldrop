# Tech debt register — Checkout team (fictional), extract

| ID | Item | Where | Cost today (evidence) | Fix size | Decision | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| TD-04 | `OrderService` does pricing, tax, stock, payment, email, cancel, refund and finance export in one 1,812-line class; every order change edits it | `orders/order_service.py` | 9 of the last 12 merged order PRs touched `order_service.py`; median review time for those PRs 3.1 days against a team median of 1.2 days; INC-702 (tax totals wrong after a discount change, Aug) and INC-715 (confirmation emails sent for failed payments, Sep) | L | Pay now | A third incident traced to `order_service.py` | Checkout team |
