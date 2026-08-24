"""Generic client for AEMET OpenData's two-step pattern.

See spec/ingest/STATIONS.md: the initial request returns a small JSON
with a temporary URL (`datos`) that must be requested again to get the
actual content, served as ISO-8859-15 (not UTF-8).
"""

import json

import requests

from ingest.config import AEMET_API_KEY

TIMEOUT = 30


class AemetError(RuntimeError):
    pass


def fetch(endpoint: str) -> list | dict:
    """Runs AEMET's two-step pattern and returns the already correctly
    decoded JSON (ISO-8859-15 -> str -> json)."""

    response = requests.get(
        endpoint, headers={"api_key": AEMET_API_KEY}, timeout=TIMEOUT
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
