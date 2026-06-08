# AlphaOS — Dashboard Operativo AI

Dashboard personale per operatività AI: chat advisor, RSS ticker, segnali trading, monitoraggio progetti.

## Deploy

```bash
# Vercel (static)
vercel --prod
```

**Live**: https://alphaos.vercel.app

## Struttura

```
alphaos/
├── index.html      # App principale (vanilla JS, ~2700 righe)
├── manifest.json   # PWA
├── sw.js           # Service Worker
├── vercel.json     # Config static
└── assets/         # Icone PWA
```

## Funzionalità

- **AI Advisor**: Chat con ensemble LLM (Gemini→Groq→OpenRouter→Ollama→Template)
- **RSS Ticker**: Feed personalizzabili
- **Trading Signals**: Segnali tecnici
- **Projects Dashboard**: Monitoraggio progetti video
- **PWA**: Installabile, offline-first

## Collegamento Video Studio

Il link "🎬 AI Video Studio" in sidebar apre la documentazione API del Video Studio separato.

---

**AlphaOS è un progetto autonomo.** Non dipende da Video Studio.