from __future__ import annotations

import httpx
from loguru import logger
from app.config import settings


class SupabaseDB:
    """Client per eseguire SQL su Supabase via Management API.
    
    Usa l'access token (sbp_...) per chiamare POST /v1/projects/{ref}/database/query
    e POST /v1/projects/{ref}/database/query (DDL).
    """

    def __init__(self):
        self.token = settings.supabase_access_token
        self.ref = settings.supabase_project_ref
        self.base_url = "https://api.supabase.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _request(self, sql: str) -> list[dict] | None:
        if not self.token:
            raise RuntimeError("SUPABASE_ACCESS_TOKEN non configurato")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/v1/projects/{self.ref}/database/query",
                headers=self.headers,
                json={"query": sql},
            )
        if resp.status_code in (200, 201):
            return resp.json()
        text = resp.text[:500]
        logger.error(f"Supabase query error ({resp.status_code}): {text}")
        raise RuntimeError(f"Query SQL fallita ({resp.status_code}): {text}")

    async def fetch_one(self, sql: str, params: dict | None = None) -> dict | None:
        """Esegue SELECT e restituisce la prima riga o None."""
        rows = await self._request(sql)
        if rows and len(rows) > 0:
            return rows[0]
        return None

    async def fetch_all(self, sql: str, params: dict | None = None) -> list[dict]:
        """Esegue SELECT e restituisce tutte le righe."""
        return await self._request(sql) or []

    async def execute(self, sql: str) -> None:
        """Esegue SQL senza ritorno (INSERT/UPDATE/DELETE)."""
        await self._request(sql)

    async def close(self):
        pass


class SupabaseDBContext:
    """Context manager per SupabaseDB (compatibile con get_db)."""

    def __init__(self):
        self.db = SupabaseDB()

    async def __aenter__(self) -> SupabaseDB:
        return self.db

    async def __aexit__(self, *args):
        await self.db.close()
