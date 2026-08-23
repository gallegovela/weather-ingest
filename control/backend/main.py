"""Arranque de la API FastAPI del panel de control.

Monta el router de cada módulo (ver spec/control/core.md,
"Organización interna de control/backend/"). Ejecución:
    cd control/backend && uvicorn main:app --reload
"""

from fastapi import FastAPI

from modulos.estaciones.router import router as estaciones_router
from modulos.seguridad.router import router as seguridad_router

app = FastAPI(title="Panel de control - weather")

app.include_router(seguridad_router)
app.include_router(estaciones_router)
