"""Cliente genérico para el patrón de dos pasos de AEMET OpenData.

Ver spec/importa/ESTACIONES.md: la primera petición devuelve un JSON
pequeño con una URL temporal (`datos`) que hay que volver a pedir para
obtener el contenido real, servido como ISO-8859-15 (no UTF-8).
"""

import json

import requests

from importa.config import AEMET_API_KEY

TIMEOUT = 30


class AemetError(RuntimeError):
    pass


def fetch(endpoint: str) -> list | dict:
    """Ejecuta el patrón de dos pasos de AEMET y devuelve el JSON ya
    decodificado correctamente (ISO-8859-15 -> str -> json)."""

    response = requests.get(
        endpoint, headers={"api_key": AEMET_API_KEY}, timeout=TIMEOUT
    )
    response.raise_for_status()
    envelope = response.json()

    if envelope.get("estado") != 200:
        raise AemetError(
            f"Respuesta inesperada de AEMET: estado={envelope.get('estado')} "
            f"descripcion={envelope.get('descripcion')!r}"
        )

    data_url = envelope.get("datos")
    if not data_url:
        raise AemetError("La respuesta de AEMET no incluye la clave 'datos'.")

    data_response = requests.get(data_url, timeout=TIMEOUT)
    data_response.raise_for_status()

    text = data_response.content.decode("ISO-8859-15")
    return json.loads(text)
