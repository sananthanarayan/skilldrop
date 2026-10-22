"""Invoice generation."""


def run_nightly():
    """Generate invoices for every customer whose billing date is today.

    Guarded by an idempotency row in `invoice_runs` keyed on the run date.
    """
    raise NotImplementedError("fixture")
