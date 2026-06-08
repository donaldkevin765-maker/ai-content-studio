from __future__ import annotations

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/video_ai.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    tts_engine: str = "gtts"
    tts_lang: str = "it"
    tts_voice_id: str = ""
    tts_speed: float = 1.0

    use_local_sd: bool = False
    sd_model_id: str = "stabilityai/stable-diffusion-2-1"
    hf_api_token: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    script_seed: int = 42

    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 30
    max_video_duration: int = 300
    subtitle_font: str = ""  # se vuoto usa FONTS_DIR/NotoSans-Regular.ttf

    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    supabase_bucket: str = "videos"

    webhook_url: Optional[str] = None
    webhook_secret: str = ""

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    notion_api_key: str = ""
    notion_database_id: str = ""

    n8n_webhook_url: Optional[str] = None

    deepl_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "mistralai/mistral-7b-instruct:free"
    openrouter_referer: str = "http://localhost:8000"
    pexels_api_key: str = ""

    default_language: str = "it"

    output_dir: str = "./output"
    assets_dir: str = "./assets"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

import os as _os
BASE_DIR = Path(__file__).resolve().parent.parent
_VERCEL = _os.environ.get("VERCEL") == "1"
_ROOT_DIR = Path(_os.environ.get("VERCEL_STARTER_DIR", str(BASE_DIR))) if _VERCEL else BASE_DIR
DATA_DIR = _ROOT_DIR / "data" if not _VERCEL else Path("/tmp/data")
OUTPUT_DIR = _ROOT_DIR / settings.output_dir if not _VERCEL else Path("/tmp/output")
ASSETS_DIR = _ROOT_DIR / settings.assets_dir
FONTS_DIR = ASSETS_DIR / "fonts"
AUDIO_DIR = OUTPUT_DIR / "audio"
IMAGES_DIR = OUTPUT_DIR / "images"
VIDEOS_DIR = OUTPUT_DIR / "videos"

for d in [DATA_DIR, OUTPUT_DIR, VIDEOS_DIR, AUDIO_DIR, IMAGES_DIR, FONTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
