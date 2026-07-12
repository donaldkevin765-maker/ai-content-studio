"""
Nano Banana / Gemini Image Generation Service
Genera immagini AI usando Google Gemini via la Nano Banana API.
Richiede GEMINI_API_KEY nell'ambiente.
"""
from __future__ import annotations

import os
import base64
from pathlib import Path
from loguru import logger
from typing import Optional
import httpx


class NanoBananaGenerator:
    """Generatore immagini AI via Gemini / Nano Banana.
    Usa il GEMINI_API_KEY dalle impostazioni del progetto.
    """

    def __init__(self):
        from app.config import settings

        self.api_key = settings.gemini_api_key or ""
        self.base_url = os.environ.get(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta",
        )
        self.model = os.environ.get(
            "GEMINI_IMAGE_MODEL",
            "gemini-2.5-flash-image-preview",
        )
        self._available = bool(self.api_key)

    @property
    def available(self) -> bool:
        return self._available

    async def generate(
        self,
        prompt: str,
        output_path: str | Path,
        aspect_ratio: str = "16:9",
        negative_prompt: str = "",
    ) -> Optional[str]:
        """
        Genera un'immagine dal prompt e la salva su disco.
        Restituisce il path se successo, None altrimenti.
        """
        if not self._available:
            logger.warning("GEMINI_API_KEY non configurato — skip Nano Banana")
            return None

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Mappa aspect ratio a dimensione
        sizes = {
            "1:1": (1024, 1024),
            "16:9": (1920, 1080),
            "9:16": (1080, 1920),
            "4:3": (1024, 768),
            "3:4": (768, 1024),
            "21:9": (1920, 822),
        }
        width, height = sizes.get(aspect_ratio, (1920, 1080))

        # Costruisci prompt
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f" (evita: {negative_prompt})"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = (
                    f"{self.base_url}/models/{self.model}:generateContent"
                    f"?key={self.api_key}"
                )

                body = {
                    "contents": [{
                        "parts": [{"text": full_prompt}],
                    }],
                    "generationConfig": {
                        "temperature": 1.0,
                        "topK": 32,
                        "topP": 1.0,
                        "maxOutputTokens": 8192,
                    },
                }

                resp = await client.post(url, json=body)
                resp.raise_for_status()
                data = resp.json()

                # Estrai immagine dalla risposta
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.error(f"Nessun candidato nella risposta Gemini: {data}")
                    return None

                parts = candidates[0].get("content", {}).get("parts", [])
                image_data = None
                for part in parts:
                    if "inlineData" in part:
                        image_data = part["inlineData"].get("data")
                        break

                if not image_data:
                    logger.error(f"Nessuna immagine nella risposta Gemini")
                    return None

                # Decodifica e salva
                img_bytes = base64.b64decode(image_data)
                output_path.write_bytes(img_bytes)

                logger.info(
                    f"Nano Banana: immagine generata in {output_path} "
                    f"({len(img_bytes)} bytes, {aspect_ratio})"
                )
                return str(output_path)

        except httpx.HTTPStatusError as e:
            logger.error(f"Nano Banana HTTP error: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            logger.error(f"Nano Banana error: {e}")

        return None
