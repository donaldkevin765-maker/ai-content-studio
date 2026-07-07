from __future__ import annotations
from loguru import logger
from app.config import settings


class NotionService:
    """Integrazione con Notion API (gratuita). Legge/scrive pagine per gestire progetti video."""

    def __init__(self):
        self.api_key = settings.notion_api_key
        self.database_id = settings.notion_database_id

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    async def create_video_project(self, title: str, topic: str, script: str = "") -> dict | None:
        if not self.api_key or not self.database_id:
            return None

        import httpx as _httpx

        url = "https://api.notion.com/v1/pages"
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Topic": {"rich_text": [{"text": {"content": topic}}]},
                "Status": {"select": {"name": "In Progress"}},
            },
        }
        if script:
            data["properties"]["Script"] = {"rich_text": [{"text": {"content": script[:2000]}}]}

        async with _httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=data, headers=self._headers())
            if resp.status_code == 401:
                logger.warning("Notion: API key non valida")
                return None
            if resp.status_code == 429:
                logger.warning("Notion: rate limit")
                return None
            if resp.is_success:
                result = resp.json()
                logger.info(f"Notion: progetto '{title}' creato ({result.get('id', '?')})")
                return result
            logger.warning(f"Notion: errore {resp.status_code}")
            return None

    async def update_project_status(self, page_id: str, status: str) -> bool:
        if not self.api_key:
            return False

        import httpx as _httpx

        url = f"https://api.notion.com/v1/pages/{page_id}"
        data = {"properties": {"Status": {"select": {"name": status}}}}

        async with _httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(url, json=data, headers=self._headers())
            return resp.is_success
