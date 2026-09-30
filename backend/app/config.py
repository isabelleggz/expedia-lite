"""Environment-backed configuration for the Expedia Lite backend."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"


def get_geoapify_api_key() -> str | None:
    """Load and return the configured Geoapify key, if it is nonblank."""

    load_dotenv(dotenv_path=ENV_FILE_PATH)
    value = os.getenv("GEOAPIFY_API_KEY")
    if value is None or not value.strip():
        return None
    return value.strip()


def get_geoapify_api_key_status() -> str:
    """Return a safe status message without exposing the key value."""

    if get_geoapify_api_key() is None:
        return "key is not configured"
    return "key is configured"
