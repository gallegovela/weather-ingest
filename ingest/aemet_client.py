"""Generic client for AEMET OpenData's two-step pattern.

See spec/ingest/STATIONS.md: the initial request returns a small JSON
with a temporary URL (`datos`) that must be requested again to get the
actual content, served as ISO-8859-15 (not UTF-8).
"""

import json

import requests

from ingest import db

TIMEOUT = 30

_api_key_cache: str | None = None


class AemetError(RuntimeError):
    pass


def _api_key() -> str:
    # Cached for the lifetime of the process: fetched from config_values
    # (see spec/db/tables.md) instead of .env, but re-reading it from the
    # database on every single AEMET request would be wasteful.
    global _api_key_cache
    if _api_key_cache is None:
        _api_key_cache = db.get_config_value("AEMET_API_KEY")
    return _api_key_cache


def fetch(endpoint: str) -> list | dict:
    """Runs AEMET's two-step pattern and returns the already correctly
    decoded JSON (ISO-8859-15 -> str -> json)."""

    response = requests.get(
        endpoint, headers={"api_key": _api_key()}, timeout=TIMEOUT
    )
    response.raise_for_status()
    envelope = response.json()

    if envelope.get("estado") != 200:
        raise AemetError(
            f"Unexpected response from AEMET: estado={envelope.get('estado')} "
            f"descripcion={envelope.get('descripcion')!r}"
        )

    data_url = envelope.get("datos")
    if not data_url:
        raise AemetError("The AEMET response doesn't include the 'datos' key.")

    data_response = requests.get(data_url, timeout=TIMEOUT)
    data_response.raise_for_status()

    text = data_response.content.decode("ISO-8859-15")
    return json.loads(text)
