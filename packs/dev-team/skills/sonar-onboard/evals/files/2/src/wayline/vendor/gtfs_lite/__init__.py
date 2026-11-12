# Vendored third-party feed parser, pinned at 2.3.1. Upstream owns this code; do not modify.
def parse_stop_times(rows):
    return [dict(zip(("trip_id", "arrival", "departure", "stop_id"), r)) for r in rows]
