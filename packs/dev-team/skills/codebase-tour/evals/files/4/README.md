# shipcalc

Shipping quote service for the storefront. Given a cart it returns the shipping
cost, loyalty discount and VAT.

## Setup

    pip install -r requirements.txt

## Run locally

    export FLASK_APP=shipcalc
    flask run

## Tests

    python -m unittest discover

## Layout

- `src/shipcalc/shipping.py` - shipping cost and free-shipping rules
- `src/shipcalc/discounts.py` - loyalty discounts
- `src/shipcalc/tax.py` - VAT
