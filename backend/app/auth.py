from __future__ import annotations

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[str]:
    """Auth disabilitata — accetta tutto, ritorna sempre anonymous."""
    return None


async def require_auth(user_id: Optional[str] = Depends(verify_token)) -> str:
    """Auth disabilitata — ritorna sempre anonymous."""
    return "anonymous"
