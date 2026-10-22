"""Load billing-api runtime settings and secrets (see ADR-0007)."""
import json
from pathlib import Path

VAULT_DIR = Path("/vault/secrets")


def load_settings() -> dict:
    db = json.loads((VAULT_DIR / "billing-db.json").read_text())
    processor = json.loads((VAULT_DIR / "processor.json").read_text())
    return {
        "db_url": db["url"],
        "processor_api_key": processor["api_key"],
    }
