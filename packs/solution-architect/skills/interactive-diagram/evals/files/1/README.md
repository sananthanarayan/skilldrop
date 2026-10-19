# Larder

Grocery ordering for small shops. Customers order on the web, the shop gets an email.

## Architecture

- `web/` - the storefront
- `api/` - order API (Flask)
- `worker/` - sends confirmation emails
- Order events go to Kafka so analytics can consume them (planned for Q3).
- Payments are taken in the shop on collection, not online.
