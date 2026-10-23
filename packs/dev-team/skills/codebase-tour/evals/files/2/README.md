# ledgerline

Turns bank-statement CSV exports into one ledger format.

## Install

    pip install -e .

## Running the tests

    python setup.py test

## Adding a bank

Drop a new module in `src/ledgerline/parsers/` and it is picked up automatically.
Each parser subclasses `BaseParser` and implements `parse_row`.
