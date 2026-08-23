"""Importación del inventario de estaciones climatológicas de AEMET.

Ver spec/importa/ESTACIONES.md para el detalle del proceso (patrón de
dos pasos de la API, codificación ISO-8859-15, transformaciones y
estrategia de upsert) y spec/db/tables.md para el esquema de destino.

Uso:
    python -m importa.estaciones
"""

import logging

from importa import aemet_client, db

ENDPOINT = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/"
    "inventarioestaciones/todasestaciones"
)

UPSERT_SQL = """
    INSERT INTO estaciones (
        indicativo, nombre, provincia, latitud, longitud,
        latitud_decimal, longitud_decimal, altitud, indsinop
    ) VALUES (
        %(indicativo)s, %(nombre)s, %(provincia)s, %(latitud)s, %(longitud)s,
        %(latitud_decimal)s, %(longitud_decimal)s, %(altitud)s, %(indsinop)s
    )
    ON CONFLICT (indicativo) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        provincia = EXCLUDED.provincia,
        latitud = EXCLUDED.latitud,
        longitud = EXCLUDED.longitud,
        latitud_decimal = EXCLUDED.latitud_decimal,
        longitud_decimal = EXCLUDED.longitud_decimal,
        altitud = EXCLUDED.altitud,
        indsinop = EXCLUDED.indsinop,
        fecha_actualizacion = now()
    RETURNING (xmax = 0) AS inserted
"""

SELECT_ACTUAL_SQL = """
    SELECT nombre, provincia, latitud, longitud,
           latitud_decimal, longitud_decimal, altitud, indsinop,
           fecha_actualizacion
    FROM estaciones
    WHERE indicativo = %(indicativo)s
    FOR UPDATE
"""

HISTORICO_SQL = """
    INSERT INTO estaciones_historico (
        estacion_indicativo, nombre, provincia, latitud, longitud,
        latitud_decimal, longitud_decimal, altitud, indsinop, fecha_cambio
    ) VALUES (
        %(indicativo)s, %(nombre)s, %(provincia)s, %(latitud)s, %(longitud)s,
        %(latitud_decimal)s, %(longitud_decimal)s, %(altitud)s, %(indsinop)s, %(fecha_cambio)s
    )
"""

# Campos de origen comparados para detectar cambios (ver spec/db/tables.md,
# tabla estaciones_historico: latitud_decimal/longitud_decimal no se
# comparan aparte por ser función determinista de latitud/longitud).
CAMPOS_COMPARABLES = (
    "nombre", "provincia", "latitud", "longitud", "altitud", "indsinop",
)
# Mismo orden que las columnas de SELECT_ACTUAL_SQL.
_COLUMNAS_ACTUAL = (
    "nombre", "provincia", "latitud", "longitud",
    "latitud_decimal", "longitud_decimal", "altitud", "indsinop",
    "fecha_actualizacion",
)

log = logging.getLogger("importa.estaciones")


def parse_coordenada(raw: str) -> float:
    """Convierte una coordenada AEMET (grados/minutos/segundos +
    hemisferio, ej. '394924N' o '025309E') a grados decimales."""

    raw = raw.strip()
    hemisferio = raw[-1].upper()
    digitos = raw[:-1]

    segundos = int(digitos[-2:])
    minutos = int(digitos[-4:-2])
    grados = int(digitos[:-4])

    decimal = grados + minutos / 60 + segundos / 3600
    if hemisferio in ("S", "W"):
        decimal = -decimal
    return round(decimal, 6)


def transform(record: dict) -> dict:
    indsinop = record.get("indsinop", "").strip()
    return {
        "indicativo": record["indicativo"].strip(),
        "nombre": record["nombre"].strip(),
        "provincia": record["provincia"].strip(),
        "latitud": record["latitud"].strip(),
        "longitud": record["longitud"].strip(),
        "latitud_decimal": parse_coordenada(record["latitud"]),
        "longitud_decimal": parse_coordenada(record["longitud"]),
        "altitud": int(record["altitud"]),
        "indsinop": indsinop or None,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    raw_records = aemet_client.fetch(ENDPOINT)
    log.info("Recibidas %d estaciones de AEMET", len(raw_records))

    insertadas = actualizadas = errores = 0
    with db.connect() as conn, conn.cursor() as cur:
        for raw in raw_records:
            try:
                record = transform(raw)

                cur.execute(SELECT_ACTUAL_SQL, record)
                fila_actual = cur.fetchone()
                if fila_actual:
                    actual = dict(zip(_COLUMNAS_ACTUAL, fila_actual))
                    if any(actual[campo] != record[campo] for campo in CAMPOS_COMPARABLES):
                        cur.execute(HISTORICO_SQL, {
                            "indicativo": record["indicativo"],
                            "fecha_cambio": actual["fecha_actualizacion"],
                            **{campo: actual[campo] for campo in CAMPOS_COMPARABLES},
                            "latitud_decimal": actual["latitud_decimal"],
                            "longitud_decimal": actual["longitud_decimal"],
                        })

                cur.execute(UPSERT_SQL, record)
                (fue_insertada,) = cur.fetchone()
                conn.commit()
                if fue_insertada:
                    insertadas += 1
                else:
                    actualizadas += 1
            except Exception:
                conn.rollback()
                errores += 1
                log.exception("Error procesando estación %r", raw.get("indicativo"))

    log.info(
        "Resumen: recibidas=%d insertadas=%d actualizadas=%d errores=%d",
        len(raw_records),
        insertadas,
        actualizadas,
        errores,
    )


if __name__ == "__main__":
    main()
