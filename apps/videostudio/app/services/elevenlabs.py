from __future__ import annotations
from loguru import logger
from app.config import settings


class ElevenLabsService:
    """Text-to-Speech via ElevenLabs API (free tier: 10k chars/mese)."""

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel (free)

    async def generate(self, text: str, output_path: str, lang: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY mancante")

        import httpx as _httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        async with _httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=data, headers=headers)
            if resp.status_code == 401:
                raise RuntimeError("ElevenLabs: API key non valida")
            if resp.status_code == 429:
                logger.warning("ElevenLabs: rate limit (free tier 10k char/mese) - fallback a gTTS")
                raise RuntimeError("rate_limit")
            if resp.status_code == 402:
                logger.warning("ElevenLabs: crediti esauriti (free tier 10k char/mese) - fallback a gTTS")
                raise RuntimeError("no_credits")
            resp.raise_for_status()

        import asyncio

        def _write():
            with open(output_path, "wb") as f:
                f.write(resp.content)

        await asyncio.to_thread(_write)

        logger.info(f"ElevenLabs TTS: {output_path} ({len(text)} chars)")
        return output_path
