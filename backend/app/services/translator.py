from __future__ import annotations
import json
import httpx
from loguru import logger
from app.config import settings


LANGUAGE_NAMES = {
    "it": "italiano",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "pt": "portuguese",
    "ja": "japanese",
    "zh": "chinese",
    "ko": "korean",
    "ar": "arabic",
    "ru": "russian",
}


class TranslatorService:
    async def translate(self, text: str, target_lang: str) -> str:
        if target_lang == settings.default_language:
            return text
        if settings.ollama_base_url:
            try:
                return await self._translate_llm(text, target_lang)
            except Exception as e:
                logger.warning(f"LLM translation fallita: {e}")
        return text

    async def _translate_llm(self, text: str, target_lang: str) -> str:
        lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        prompt = f"Traduci il seguente testo in {lang_name}. Rispondi SOLO con la traduzione, nient'altro:\n\n{text}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
        return resp.json().get("response", text)
