# Tech debt register — billing squad

| ID | Item | Pain | Owner | Raised |
|----|------|------|-------|--------|
| DEBT-09 | Payment retries use sleep() in request thread | Slow checkout under load | payments | 2025-11 |
| DEBT-14 | `src/billing/invoice.py::build_invoice` is one giant function with 9 keyword args; no unit tests | Every pricing change touches it; 2 billing incidents in Q3 traced to edits here (wrong proration, coupon applied after tax). Adding a new tax region took a dev most of a sprint. | billing | 2026-07 |
| DEBT-15 | Float money arithmetic throughout billing | Cent-level mismatches finance fixes by hand monthly | billing | 2026-07 |
