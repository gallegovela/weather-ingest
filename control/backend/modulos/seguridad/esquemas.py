"""Modelos Pydantic de petición/respuesta del módulo seguridad.

Ver spec/control/module/seguridad.md.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    login: EmailStr
    contrasena: str


class UsuarioOut(BaseModel):
    id: int
    login: str
    fecha_alta: datetime
    fecha_actualizacion: datetime


class UsuarioCrear(BaseModel):
    login: EmailStr
    contrasena: str


class UsuarioEditar(BaseModel):
    login: EmailStr | None = None
    contrasena: str | None = None
