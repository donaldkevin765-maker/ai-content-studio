from __future__ import annotations
from pathlib import Path
from loguru import logger
from app.config import settings


class TextToSpeechService:
    async def generate(self, text: str, output_path: str, lang: str | None = None) -> str:
        engine = settings.tts_engine
        lang = lang or settings.tts_lang

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if engine == "coqui":
            return await self._coqui(text, str(out), lang)
        elif engine == "pyttsx3":
            return self._pyttsx3(text, str(out))
        elif engine == "elevenlabs":
            return await self._elevenlabs(text, str(out), lang)
        else:
            return await self._gtts(text, str(out), lang)

    async def _elevenlabs(self, text: str, output_path: str, lang: str | None = None) -> str:
        try:
            from app.services.elevenlabs import ElevenLabsService
            svc = ElevenLabsService()
            return await svc.generate(text, output_path, lang)
        except RuntimeError as e:
            err = str(e)
            if err in ("rate_limit", "no_credits"):
                logger.warning(f"ElevenLabs: {err}, fallback a gTTS")
                return await self._gtts(text, output_path, lang or settings.tts_lang)
            logger.warning(f"ElevenLabs non disponibile ({err}), fallback a gTTS")
            return await self._gtts(text, output_path, lang or settings.tts_lang)
        except Exception as e:
            logger.warning(f"ElevenLabs errore ({e}), fallback a gTTS")
            return await self._gtts(text, output_path, lang or settings.tts_lang)

    async def _gtts(self, text: str, output_path: str, lang: str) -> str:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            logger.info(f"Audio gTTS: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Errore gTTS: {e}")
            raise

    async def _coqui(self, text: str, output_path: str, lang: str) -> str:
        try:
            from TTS.api import TTS as CoquiTTS

            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            tts = CoquiTTS(model_name)
            tts.tts_to_file(
                text=text,
                file_path=output_path,
                language=lang,
                speed=settings.tts_speed,
            )
            logger.info(f"Audio Coqui TTS: {output_path}")
            return output_path
        except ImportError:
            logger.warning("Coqui TTS non installato, fallback a gTTS")
            return await self._gtts(text, output_path, lang)
        except Exception as e:
            logger.error(f"Errore Coqui TTS: {e}")
            return await self._gtts(text, output_path, lang)

    def _pyttsx3(self, text: str, output_path: str) -> str:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            logger.info(f"Audio pyttsx3: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Errore pyttsx3: {e}")
            raise
