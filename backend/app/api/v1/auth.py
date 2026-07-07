from __future__ import annotations

import hashlib
import secrets
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse

router = APIRouter()


def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with a random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a PBKDF2 hash."""
    try:
        salt, hashed = stored.split(":", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return dk.hex() == hashed
    except (ValueError, AttributeError):
        return False


def _generate_token() -> str:
    """Generate a permanent API token."""
    return "sk-" + secrets.token_hex(32)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Registra un nuovo utente e restituisce un token permanente."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email già registrata",
        )

    # Validate email format
    if "@" not in data.email or "." not in data.email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email non valida",
        )

    user = User(
        email=data.email,
        password_hash=_hash_password(data.password),
        token=_generate_token(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Nuovo utente registrato: {user.email} (id={user.id})")

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        token=user.token,
        message="Registrazione completata. Conserva questo token per accedere alle API.",
    )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Effettua il login con email e password, restituisce il token permanente."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non validi",
        )

    logger.info(f"Login effettuato: {user.email} (id={user.id})")

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        token=user.token,
        message="Login effettuato con successo.",
    )
