# RFC-015: Lock the price for the duration of checkout

Status: Accepted
Date: 2024-01-09
Author: J. Lindqvist
Amends: RFC-012
Governs: shopfront/checkout/lock.py

## Context
Customers were charged a different price from the one shown when a price changed mid-checkout.

## Decision
When a cart enters checkout, the price a customer saw must be the price they are charged for
15 minutes. We do this by reusing the pricing cache: checkout keeps the cached price for each
SKU in the cart alive for 15 minutes.
