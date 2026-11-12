import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_key: str
    log_level: str


def load_settings() -> Settings:
    api_key = os.environ.get("SHIPCALC_API_KEY")
    if not api_key:
        raise RuntimeError("SHIPCALC_API_KEY must be set (see .env.example)")
    return Settings(api_key=api_key, log_level=os.environ.get("SHIPCALC_LOG_LEVEL", "info"))
