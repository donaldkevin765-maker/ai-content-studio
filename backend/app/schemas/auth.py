from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="Email dell'utente")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 caratteri)")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email dell'utente")
    password: str = Field(..., description="Password dell'utente")


class AuthResponse(BaseModel):
    user_id: int
    email: str
    token: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
