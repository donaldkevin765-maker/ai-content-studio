from __future__ import annotations
import asyncio
import random
import struct
from pathlib import Path
from typing import Optional
from loguru import logger
from app.config import settings


class BackgroundMusicService:
    """Genera o sceglie musica di sottofondo gratuita per il video."""

    async def generate(
        self, style: str, duration: float, output_path: str, topic: str = ""
    ) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Prova HuggingFace MusicGen (se c'è API token)
        if settings.hf_api_token:
            try:
                return await self._musicgen(style, duration, str(out), topic)
            except Exception as e:
                logger.warning(f"MusicGen fallito ({e}), fallback algoritmico")

        # Fallback: musica algoritmica di qualita
        return self._algorithmic(style, duration, str(out))

    async def _musicgen(self, style: str, duration: float, output_path: str, topic: str) -> str:
        import httpx

        # Prompt musicale in base allo stile del video
        music_prompts = {
            "informativo": "calm atmospheric ambient background music for documentary",
            "divertente": "upbeat cheerful ukulele background music",
            "serio": "dramatic orchestral cinematic background music",
            "motivazionale": "epic inspirational cinematic orchestral music",
            "didattico": "soft educational piano background music",
        }
        prompt = music_prompts.get(style, "ambient background music")
        if topic:
            prompt += f" about {topic}"

        api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
        headers = {"Authorization": f"Bearer {settings.hf_api_token}"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": int(duration * 20)},
                },
            )
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)

        logger.info(f"Musica MusicGen generata: {output_path}")
        return output_path

    def _algorithmic(self, style: str, duration: float, output_path: str) -> str:
        """Genera musica algoritmica semplice ma piacevole usando suoni sinusoidali."""
        import wave
        import math

        sr = 44100
        n_frames = int(sr * duration)

        # Parametri musicali in base allo stile
        style_params = {
            "informativo": {"bpm": 70, "keys": [261, 329, 391, 349]},  # C4, E4, G4, F4
            "divertente": {"bpm": 110, "keys": [392, 440, 523, 587]},  # G4, A4, C5, D5
            "serio": {"bpm": 55, "keys": [220, 261, 329, 392]},  # A3, C4, E4, G4
            "motivazionale": {"bpm": 85, "keys": [261, 329, 392, 523]},  # C4, E4, G4, C5
            "didattico": {"bpm": 65, "keys": [293, 349, 392, 440]},  # D4, F4, G4, A4
        }
        params = style_params.get(style, style_params["informativo"])
        bpm = params["bpm"]
        keys = params["keys"]
        beat_duration = 60.0 / bpm

        samples = []
        beat = 0
        phase = 0.0
        note_idx = 0

        rng = random.Random(hash(style) + int(duration))

        for i in range(n_frames):
            t = i / sr
            beat_pos = (t % beat_duration) / beat_duration

            # Cambia nota ogni 2-4 battiti
            if beat_pos < 0.01 and rng.random() < 0.05:
                note_idx = rng.randint(0, len(keys) - 1)

            freq = keys[note_idx]

            # Onda principale (fondamentale + armoniche)
            val = (
                math.sin(2 * math.pi * freq * t)
                + 0.4 * math.sin(2 * math.pi * freq * 2 * t)
                + 0.2 * math.sin(2 * math.pi * freq * 3 * t)
            )

            # Volume che decresce gradualmente
            envelope = 0.08 * (1 - t / duration * 0.5)
            val *= envelope

            # Lieve tremolo per atmosfera
            val *= 0.9 + 0.1 * math.sin(2 * math.pi * 5 * t)

            # Piatto hi-hat ogni 2 battiti
            if beat_pos < 0.02 and int(t / beat_duration) % 2 == 0:
                hat = rng.random() * 0.05 * math.exp(-t * 50 * beat_duration)
                val += hat

            samples.append(val)

            if beat_pos > 0.99:
                beat += 1

        # Normalizza e scrivi WAV
        max_val = max(abs(s) for s in samples) or 1
        samples_16 = [int(s / max_val * 16384) for s in samples]

        with wave.open(output_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(struct.pack(f"<{len(samples_16)}h", *samples_16))

        logger.info(f"Musica algoritmica: {output_path} (stile={style}, bpm={bpm})")
        return output_path
