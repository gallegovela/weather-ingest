"""Pydantic request/response models for the security module.

See spec/control/module/security.md.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    login: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    login: str
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    login: EmailStr
    password: str


class UserUpdate(BaseModel):
    login: EmailStr | None = None
    password: str | None = None


class SessionOut(BaseModel):
    id: int
    login: str
