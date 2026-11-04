# billing-batch

Nightly batch jobs for Hartwell Water billing.

## feecalc (legacy)

`legacy/feecalc.py` reads the nightly fixed-width account extract and writes the late-fee
file that the billing system uploads at 02:00. The billing upload parses the fee file
strictly: header line, one `account,NAME,days,fee` line per charged account, and the
`# TOTAL` trailer. It rejects the whole file if the trailer total doesn't match the lines.

    python3 legacy/feecalc.py samples/accounts_2026-10.txt 20261031

Sample extracts are in `samples/`. They are anonymised copies of real extract rows plus
some edge cases ops collected.

Tests: `python3 -m unittest discover -s tests`
