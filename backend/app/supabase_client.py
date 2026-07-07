from __future__ import annotations
from typing import Optional
from pathlib import Path
import httpx
from loguru import logger
from app.config import settings


class SupabaseStorage:
    def __init__(self, url: Optional[str] = None, service_key: Optional[str] = None):
        self.url = url or settings.supabase_url
        self.service_key = service_key or settings.supabase_service_key
        self.bucket = settings.supabase_bucket

    async def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=f"{self.url}/storage/v1",
            headers={
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}",
            },
            timeout=120.0,
        )

    async def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        if not self.url or not self.service_key:
            logger.warning("Supabase non configurato, salto upload")
            return None
        async with await self._client() as client:
            with open(local_path, "rb") as f:
                resp = await client.post(
                    f"/object/{self.bucket}/{remote_path}",
                    content=f.read(),
                    headers={"content-type": "application/octet-stream"},
                )
            if resp.is_success:
                public_url = f"{self.url}/storage/v1/object/public/{self.bucket}/{remote_path}"
                logger.info(f"Upload Supabase: {public_url}")
                return public_url
            logger.error(f"Errore upload Supabase: {resp.status_code} {resp.text}")
            return None

    async def delete_file(self, remote_path: str) -> bool:
        if not self.url or not self.service_key:
            return False
        async with await self._client() as client:
            resp = await client.delete(f"/object/{self.bucket}/{remote_path}")
            if not resp.is_success:
                logger.error(f"Errore delete Supabase: {resp.status_code}")
            return resp.is_success

    async def list_files(self, folder: str = "") -> list[str]:
        if not self.url or not self.service_key:
            return []
        async with await self._client() as client:
            resp = await client.get(f"/object/list/{self.bucket}", params={"prefix": folder})
            if resp.is_success:
                return [item["name"] for item in resp.json()]
            return []

    async def download_file(self, remote_path: str, local_path: str) -> Optional[str]:
        """Scarica un file da Supabase Storage."""
        if not self.url or not self.service_key:
            return None
        async with await self._client() as client:
            resp = await client.get(f"/object/public/{self.bucket}/{remote_path}")
            if resp.is_success:
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                return local_path
            logger.error(f"Errore download Supabase: {resp.status_code} {resp.text}")
            return None

    async def get_public_url(self, remote_path: str) -> Optional[str]:
        if not self.url:
            return None
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{remote_path}"


def get_supabase_storage() -> SupabaseStorage:
    return SupabaseStorage()
