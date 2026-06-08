from __future__ import annotations
import hashlib
import hmac
import time
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str | None:
    if not settings.supabase_jwt_secret:
        return None
    if not credentials:
        raise HTTPException(status_code=401, detail="Token mancante")
    token = credentials.credentials
    try:
        import jwt
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
        return payload.get("sub")
    except ImportError:
        return None
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")


def require_auth(user_id: str | None = Depends(verify_token)) -> str:
    if settings.supabase_jwt_secret and not user_id:
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")
    return user_id or "anonymous"
