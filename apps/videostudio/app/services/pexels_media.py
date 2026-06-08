from __future__ import annotations
import random
from pathlib import Path
from loguru import logger
from app.config import settings


class PexelsMedia:
    """Stock video/foto gratuiti da Pexels API (gratuito, con attribuzione).

    Prendi API key su https://www.pexels.com/api/
    Metti PEXELS_API_KEY nel .env
    """

    def __init__(self):
        self.api_key = settings.pexels_api_key

    async def search_video(self, query: str, min_duration: int = 10) -> str | None:
        if not self.api_key:
            return None
        import httpx as _httpx
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": 5, "min_duration": min_duration, "orientation": "landscape"}
        try:
            async with _httpx.AsyncClient(timeout=10.0) as c:
                resp = await c.get(url, params=params, headers=headers)
                if resp.status_code == 429:
                    logger.warning("Pexels: rate limit")
                    return None
                resp.raise_for_status()
                data = resp.json()
                videos = data.get("videos", [])
                if not videos:
                    logger.info(f"Pexels: nessun video per '{query}'")
                    return None
                best = videos[0]
                files = best.get("video_files", [])
                if not files:
                    return None
                hd = [f for f in files if f.get("height", 0) >= 720]
                chosen = hd[0] if hd else files[0]
                logger.info(f"Pexels: video '{query}' ({chosen.get('width', '?')}x{chosen.get('height', '?')})")
                return chosen.get("link")
        except Exception as e:
            logger.warning(f"Pexels video search errore: {e}")
            return None

    async def search_image(self, query: str) -> str | None:
        if not self.api_key:
            return None
        import httpx as _httpx
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": 5, "orientation": "landscape"}
        try:
            async with _httpx.AsyncClient(timeout=10.0) as c:
                resp = await c.get(url, params=params, headers=headers)
                resp.raise_for_status()
                photos = resp.json().get("photos", [])
                if not photos:
                    return None
                selected = random.choice(photos[:3])
                src = selected.get("src", {})
                url = src.get("large") or src.get("original")
                logger.info(f"Pexels: foto '{query}' ({url})")
                return url
        except Exception as e:
            logger.warning(f"Pexels image search errore: {e}")
            return None
