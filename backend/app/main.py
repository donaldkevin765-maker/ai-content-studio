from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import init_db
from app.api.v1 import projects, videos, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inizializzazione database...")
    ok = await init_db()
    if ok:
        logger.info("Database pronto")
    else:
        logger.warning("Database non inizializzato (manca DATABASE_URL) - l'app funzionerà in modalità limitata")
    yield
    logger.info("Arresto")


app = FastAPI(
    title="Sistema Video AI Automatico",
    description="API per la generazione automatica di video con AI - 100% gratuita/open-source",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])


@app.get("/api/v1/services")
async def list_services():
    from app.config import settings as _s
    return {
        "tts": {
            "available": ["gtts", "pyttsx3", "elevenlabs"],
            "configured": _s.tts_engine,
            "elevenlabs": bool(_s.elevenlabs_api_key),
            "info": "gTTS (illimitato), ElevenLabs (10k chars/mese)",
        },
        "llm": {
            "gemini": bool(_s.gemini_api_key),
            "groq": bool(_s.groq_api_key),
            "openrouter": bool(_s.openrouter_api_key),
            "ollama": bool(_s.ollama_base_url and "localhost" not in _s.ollama_base_url),
            "info": "Gemini (60 req/min), Groq (30 req/min), OpenRouter ($1 gratis poi free models)",
        },
        "translation": {
            "deepl": bool(_s.deepl_api_key),
            "google_fallback": True,
            "info": "DeepL (500k char/mese), fallback Google Translate",
        },
        "stock_media": {
            "pexels": bool(_s.pexels_api_key),
            "info": "Pexels (gratuito con attribuzione, video+foto stock)",
        },
        "music": {
            "musicgen": bool(_s.hf_api_token),
            "placeholder": True,
            "info": "MusicGen via HF API (gratis), o placeholder sintetico",
        },
        "stt": {
            "whisper": True,
            "info": "Whisper open source (self-hosted, scarica modello ~1.5GB alla prima run)",
        },
        "automation": {
            "n8n": bool(_s.webhook_url or _s.n8n_webhook_url),
            "info": "n8n open source: docker run -it --rm -p 5678:5678 n8nio/n8n",
        },
        "project_management": {
            "notion": bool(_s.notion_api_key and _s.notion_database_id),
            "info": "API Notion gratuita: https://www.notion.so/my-integrations",
        },
        "free_forever": {
            "info": "Whisper, MusicGen placeholder, gTTS, Google Translate fallback, Ollama (locale), HuggingFace Inference API - tutti gratis senza limiti",
        },
    }


@app.get("/")
async def root():
    return {
        "status": "ok",
        "app": "Sistema Video AI Automatico",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "projects": "/api/v1/projects/",
            "videos": "/api/v1/videos/",
        },
        "note": "Serverless: for persistent storage set DATABASE_URL env var (Postgres)",
    }


@app.get("/health")
async def health():
    checks = {"database": "ok", "redis": "ok", "supabase": "ok"}
    issues = []

    try:
        from app.database import DBContext
        async with DBContext() as db:
            await db.fetch_one("SELECT 1 as test")
    except Exception as e:
        checks["database"] = f"error: {e}"
        issues.append("database")

    try:
        from redis import Redis
        r = Redis.from_url(settings.celery_broker_url)
        r.ping()
        r.close()
    except Exception as e:
        checks["redis"] = f"error: {e}"
        issues.append("redis")

    if settings.supabase_url:
        try:
            import httpx
            key = settings.supabase_service_key or settings.supabase_anon_key or ""
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{settings.supabase_url}/rest/v1/",
                    headers={"apikey": key, "Authorization": f"Bearer {key}"},
                )
                if not resp.is_success:
                    checks["supabase"] = f"error: {resp.status_code}"
                    issues.append("supabase")
                else:
                    checks["supabase"] = "ok"
        except Exception as e:
            checks["supabase"] = f"error: {e}"
            issues.append("supabase")
    else:
        checks["supabase"] = "not configured"

    return {"status": "healthy" if not issues else "degraded", "checks": checks}


def run():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
