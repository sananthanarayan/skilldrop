"""Internal-caller authentication for billing-api."""
from .hmac_verify import require_hmac_signature as require_internal_caller

__all__ = ["require_internal_caller"]
