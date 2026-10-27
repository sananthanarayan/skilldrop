"""Check the peer certificate's SPIFFE ID on internal requests (see ADR-0011)."""
from functools import wraps

ALLOWED_PEERS = {
    "spiffe://tallowmere.internal/billing-api",
}
CA_BUNDLE = "/etc/ironbark/ca-bundle.pem"


def require_peer_identity(handler):
    @wraps(handler)
    def wrapper(event, peer_cert, *args, **kwargs):
        spiffe_id = peer_cert.get("uri_san", "")
        if spiffe_id not in ALLOWED_PEERS:
            raise PermissionError(f"peer {spiffe_id!r} not allowed")
        return handler(event, peer_cert, *args, **kwargs)

    return wrapper
