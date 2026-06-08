# Video Studio — AI Video Generation Pipeline

Sistema end-to-end per generare video con AI: topic → script → TTS → immagini → musica → montaggio → MP4. **100% gratuito, open-source.**

## Architettura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Topic     │───▶│  LLM        │───▶│  TTS        │───▶│  Immagini   │
│  + Stile    │    │  Ensemble   │    │  (gTTS/     │    │  (Pexels/   │
│  + Durata   │    │  (Gemini→   │    │   ElevenLabs)│   │   HF/       │
└─────────────┘    │  Groq→      │    └─────────────┘    │   Placeholder)│
                   │  OpenRouter)│         │             └─────────────┘
                   └──────┬──────┘         │                   │
                          │                ▼                   ▼
                   ┌─────────────┐  ┌─────────────┐    ┌─────────────┐
                   │  Musica     │  │  Sottotitoli │    │  Montaggio  │
                   │  (MusicGen/ │  │  (Whisper)  │    │  (MoviePy+  │
                   │  Placeholder)│  └─────────────┘    │   FFmpeg)   │
                   └──────┬──────┘          │           └──────┬──────┘
                          │                 │                  │
                          └─────────────────┼──────────────────┘
                                            ▼
                                      ┌─────────────┐
                                      │  Video MP4  │
                                      └─────────────┘
```

## Stack

- **API**: FastAPI + SQLAlchemy 2.0 + SQLite/PostgreSQL
- **Queue**: Celery + Redis (rendering pesante)
- **LLM**: Gemini / Groq / OpenRouter / Ollama / Template (fallback automatico)
- **TTS**: gTTS / ElevenLabs (free tier)
- **Immagini**: Pexels / HuggingFace SD / Placeholder
- **Musica**: MusicGen (HF) / audiocraft / numpy synth
- **STT**: Whisper (open source)
- **Deploy**: Vercel (serverless) + Railway/Render (worker)

## Quick Start

```bash
cd videostudio
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Opzionale: aggiungi API key in .env per qualità superiore
python -m uvicorn app.main:app --reload
```

Poi: `http://localhost:8000/docs` → crea progetto → crea video → genera script → render.

## API Endpoints

| Metodo | Endpoint | Descrizione |
|---|---|---|
| `POST` | `/api/v1/projects/` | Crea progetto |
| `POST` | `/api/v1/videos/` | Crea video (pending) |
| `POST` | `/videos/{id}/generate-script` | Genera script con LLM ensemble |
| `POST` | `/videos/{id}/render` | Avvia rendering |
| `GET` | `/videos/{id}/progress` | Polling stato real-time |
| `GET` | `/api/v1/services` | Stato tutti i 10+ servizi AI |

## 10+ Servizi AI — Tutti Gratis

| Categoria | Servizi | Tier |
|---|---|---|
| **LLM Script** | Gemini (60/min), Groq (30/min), OpenRouter, Ollama, Template | ✅ |
| **TTS** | ElevenLabs (10k/mese), gTTS | ✅ |
| **Traduzione** | DeepL (500k/mese), Google Translate | ✅ |
| **Immagini** | Pexels, HF Stable Diffusion, Placeholder | ✅ |
| **Musica** | MusicGen (HF), audiocraft, numpy synth | ✅ |
| **STT/Sottotitoli** | Whisper (open source) | ✅ |
| **Automazione** | n8n (self-host) | ✅ |
| **Project Mgmt** | Notion API | ✅ |

**Nessun pagamento richiesto** — fallback automatico a catena. Se manca API key → usa il successivo.

## Deploy

### Vercel (API Serverless)
```bash
vercel --prod
```
Live: https://sistema-video-ai.vercel.app

### Worker Rendering (per video pesanti)
```bash
# Railway / Render / Fly.io
celery -A app.workers.celery_app worker --loglevel=info
```

## Configurazione (.env)

Copia `.env.example` → `.env` e aggiungi le API key opzionali:

| Chiave | Servizio | Link |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini | https://aistudio.google.com/apikey |
| `GROQ_API_KEY` | Groq | https://console.groq.com/keys |
| `OPENROUTER_API_KEY` | OpenRouter | https://openrouter.ai/keys |
| `DEEPL_API_KEY` | DeepL | https://www.deepl.com/pro-api |
| `ELEVENLABS_API_KEY` | ElevenLabs | https://elevenlabs.io/app |
| `PEXELS_API_KEY` | Pexels | https://www.pexels.com/api/ |
| `HF_API_TOKEN` | HuggingFace | https://huggingface.co/settings/tokens |
| `NOTION_API_KEY` + `NOTION_DATABASE_ID` | Notion | https://www.notion.so/my-integrations |

**Senza nessuna chiave** → tutto funziona con fallback (template, gTTS, Google Translate, placeholder).

## Test

```bash
pytest tests/ -v
# 37/37 passano
```

---

**Video Studio è un progetto autonomo.** Non dipende da AlphaOS.