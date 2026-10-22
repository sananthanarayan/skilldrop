"""Internal-caller authentication for ledger-worker."""
from .mtls import require_peer_identity as require_internal_caller

__all__ = ["require_internal_caller"]
