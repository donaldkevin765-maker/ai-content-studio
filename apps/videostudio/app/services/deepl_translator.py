from __future__ import annotations
from loguru import logger
from app.config import settings


class DeepLTranslator:
    """Traduzioni con DeepL API (gratuito: 500k caratteri/mese).

    Registrati su https://www.deepl.com/pro-api (free tier)
    Metti DEEPL_API_KEY nel .env
    """

    def __init__(self):
        self.api_key = settings.deepl_api_key
        self._base = "https://api-free.deepl.com/v2"

    async def translate(self, text: str, target_lang: str = "IT", source_lang: str | None = None) -> str:
        if not self.api_key:
            return await self._google_fallback(text, target_lang)
        import httpx as _httpx
        data = {"text": [text], "target_lang": target_lang.upper()}
        if source_lang:
            data["source_lang"] = source_lang.upper()
        try:
            async with _httpx.AsyncClient(timeout=10.0) as c:
                resp = await c.post(f"{self._base}/translate", data=data, headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"})
                if resp.status_code == 456:
                    logger.warning("DeepL: quota 500k/mese esaurita, fallback Google Translate")
                    return await self._google_fallback(text, target_lang)
                if resp.status_code == 429:
                    logger.warning("DeepL: rate limit, fallback Google Translate")
                    return await self._google_fallback(text, target_lang)
                resp.raise_for_status()
                return resp.json()["translations"][0]["text"]
        except Exception as e:
            logger.warning(f"DeepL errore ({e}), fallback Google Translate")
            return await self._google_fallback(text, target_lang)

    async def _google_fallback(self, text: str, target_lang: str) -> str:
        try:
            from deep_translator import GoogleTranslator
            import asyncio
            result = await asyncio.to_thread(
                GoogleTranslator(source="auto", target=target_lang.lower()).translate, text
            )
            return result
        except ImportError:
            logger.warning("deep_translator non installato, restituisco testo originale")
            return text
        except Exception as e:
            logger.warning(f"Google Translate fallback fallito: {e}")
            return text
