"""Session store backed by Redis (ADR-0003)."""

SESSION_TTL_SECONDS = 8 * 60 * 60


def load_session(session_id):
    raise NotImplementedError
