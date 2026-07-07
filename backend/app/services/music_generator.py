from __future__ import annotations
from pathlib import Path
from loguru import logger


class MusicGenerator:
    """Genera musica di sottofondo per video.

    Opzione 1: HuggingFace API (gratis, con HF_API_TOKEN)
    Opzione 2: MusicGen via audiocraft (self-hosted, gratis)
    Opzione 3: loop audio placeholder generato con numpy
    """

    def __init__(self):
        from app.config import settings
        self.hf_token = settings.hf_api_token
        self.model = "facebook/musicgen-small"

    async def generate(self, prompt: str, output_path: str, duration: int = 30) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if self.hf_token:
            return await self._huggingface(prompt, str(out), duration)

        try:
            return await self._audiocraft(prompt, str(out), duration)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"MusicGen self-hosted fallito: {e}")

        return await self._placeholder(str(out), duration)

    async def _huggingface(self, prompt: str, output_path: str, duration: int) -> str:
        import httpx as _httpx
        api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": f"{prompt}, instrumental, background music", "parameters": {"duration": duration}}
        async with _httpx.AsyncClient(timeout=120.0) as c:
            resp = await c.post(api_url, json=payload, headers=headers)
            if resp.status_code == 429:
                logger.warning("HF MusicGen: rate limit, genero placeholder")
                return await self._placeholder(output_path, duration)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)
        logger.info(f"MusicGen HF: {output_path} ({duration}s)")
        return output_path

    async def _audiocraft(self, prompt: str, output_path: str, duration: int) -> str:
        import torchaudio
        from audiocraft.models import MusicGen as _MGen
        from audiocraft.data.audio import audio_write

        model = _MGen.get_pretrained("facebook/musicgen-small")
        model.set_generation_params(duration=duration)
        wav = model.generate([f"{prompt}, instrumental background music"], progress=False)
        for idx, one_wav in enumerate(wav):
            audio_write(output_path.replace(".wav", ""), one_wav.cpu(), model.sample_rate, format="wav")
        logger.info(f"MusicGen locale: {output_path} ({duration}s)")
        return output_path

    async def _placeholder(self, output_path: str, duration: int) -> str:
        import numpy as np
        import soundfile as sf
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        wave = 0.3 * np.sin(440 * 2 * np.pi * t)
        wave += 0.15 * np.sin(330 * 2 * np.pi * t)
        wave += 0.1 * np.sin(220 * 2 * np.pi * t)
        envelope = np.exp(-t / (duration * 0.4))
        wave *= envelope
        sf.write(output_path, wave.astype(np.float32), sr)
        logger.info(f"Musica placeholder: {output_path} ({duration}s)")
        return output_path
