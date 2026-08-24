"""Startup of the control panel's FastAPI API.

Mounts each module's router (see spec/control/core.md, "Internal
organization of control/backend/"). Run with:
    cd control/backend && uvicorn main:app --reload
"""

from fastapi import FastAPI

from modules.stations.router import router as stations_router
from modules.security.router import router as security_router

app = FastAPI(title="Panel de control - weather")

app.include_router(security_router)
app.include_router(stations_router)
