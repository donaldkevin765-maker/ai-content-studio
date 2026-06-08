# AI Content Studio — Monorepo Unificato

**Un unico repo per tutto l'ecosistema AI: AlphaOS (Dashboard) + VideoStudio (Pipeline Video).**

## Struttura

```
ai-content-studio/
├── apps/
│   ├── alphaos/           # Dashboard AI (PWA, vanilla JS)
│   │   ├── index.html
│   │   ├── manifest.json
│   │   ├── sw.js
│   │   └── vercel.json
│   │
│   └── videostudio/       # Pipeline Video AI (FastAPI + Celery)
│       ├── app/           # Backend FastAPI
│       │   ├── main.py
│       │   ├── api/       # REST endpoints
│       │   ├── services/  # 10+ servizi AI gratuiti
│       │   ├── workers/   # Celery tasks
│       │   └── models/    # SQLAlchemy models
│       ├── index.html     # Frontend React (servito su /*)
│       ├── pyproject.toml
│       ├── vercel.json
│       ├── Dockerfile.api
│       ├── Dockerfile.worker
│       └── tests/
│
├── docker-compose.yml     # Ambiente locale completo
├── nginx.alphaos.conf     # Config nginx per AlphaOS
├── package.json           # Workspaces + script deploy
├── vercel.json            # Root config (routing)
└── README.md
```

## Deploy Online (Live)

| Servizio | URL | Descrizione |
|---|---|---|
| **AlphaOS** | https://alphaos.vercel.app | Dashboard AI (PWA) |
| **VideoStudio API** | https://sistema-video-ai.vercel.app | Backend FastAPI |
| **API Docs** | https://sistema-video-ai.vercel.app/docs | Swagger UI |
| **Stato Servizi** | https://sistema-video-ai.vercel.app/api/v1/services | 10+ servizi AI |

## Quick Start Locale

```bash
# 1. Installa dipendenze root
npm install

# 2. Avvia tutto (Postgres, Redis, Ollama, API, Worker, AlphaOS)
docker-compose up -d

# 3. Verifica
# AlphaOS:      http://localhost:3000
# API:          http://localhost:8000/docs
# Health:       http://localhost:8000/health
```

## Servizi AI — Tutti Gratis

| Categoria | Servizi | Tier |
|---|---|---|
| **LLM Script** | Gemini (60/min), Groq (30/min), OpenRouter, Ollama, Template | ✅ |
| **TTS** | ElevenLabs (10k/mese), gTTS | ✅ |
| **Traduzione** | DeepL (500k/mese), Google Translate | ✅ |
| **Immagini** | Pexels, HF Stable Diffusion, Placeholder | ✅ |
| **Musica** | MusicGen (HF), audiocraft, numpy synth | ✅ |
| **STT** | Whisper (open source) | ✅ |
| **Automazione** | n8n (self-host) | ✅ |
| **Project Mgmt** | Notion API | ✅ |

**Zero costi** — fallback automatico. Senza API key → usa il successivo.

## Configurazione

Copia `apps/videostudio/.env.example` → `apps/videostudio/.env` e aggiungi API key opzionali:

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

**Senza nessuna chiave** → tutto funziona con fallback gratuiti.

## Deploy Vercel

```bash
# AlphaOS (static)
cd apps/alphaos && vercel --prod

# VideoStudio API (serverless)
cd apps/videostudio && vercel --prod

# Oppure dal root:
npm run deploy:alphaos
npm run deploy:videostudio
```

**URL Live:**
- AlphaOS: https://alphaos.vercel.app
- VideoStudio API: https://sistema-video-ai.vercel.app
- Docs: https://sistema-video-ai.vercel.app/docs

## Test

```bash
cd apps/videostudio
pytest tests/ -v
# 37/37 passano
```

## Worker Rendering (per video pesanti)

Il rendering video richiede FFmpeg e CPU/GPU. Deploy su Railway/Render/Fly.io:

```bash
# Su Railway/Render
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

## Licenza

MIT — Open Source, gratuito per sempre.