from __future__ import annotations
from typing import Optional
from pathlib import Path
from loguru import logger


class WhisperSTT:
    """Speech-to-text con Whisper (open source, self-hostato, gratis).

    Installa: pip install openai-whisper
    Prima run scarica il modello (~1.5GB per tiny, ~3GB per base).
    """

    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self._model = None

    def _load(self):
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self.model_size)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        self._load()
        opts = {"task": "transcribe"}
        if language:
            opts["language"] = language
        result = self._model.transcribe(audio_path, **opts)
        logger.info(f"Whisper: trascritti {len(result.get('segments', []))} segmenti da {audio_path}")
        return result

    def transcribe_to_srt(self, audio_path: str, output_path: str, language: Optional[str] = None) -> str:
        result = self.transcribe(audio_path, language)
        segments = result.get("segments", [])
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = self._srt_time(seg["start"])
                end = self._srt_time(seg["end"])
                text = seg["text"].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        logger.info(f"SRT generato: {output_path} ({len(segments)} segmenti)")
        return str(out)

    def _srt_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    async def atranscribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        import asyncio
        return await asyncio.to_thread(self.transcribe, audio_path, language)

    async def atranscribe_to_srt(self, audio_path: str, output_path: str, language: Optional[str] = None) -> str:
        import asyncio
        return await asyncio.to_thread(self.transcribe_to_srt, audio_path, output_path, language)
