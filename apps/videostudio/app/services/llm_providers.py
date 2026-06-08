from __future__ import annotations
from loguru import logger
from app.config import settings


class GeminiProvider:
    """Google Gemini API (gratuito: 60 richieste/minuto).

    Prendi API key su https://aistudio.google.com/apikey
    Metti GEMINI_API_KEY nel .env
    """

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = "models/gemini-2.0-flash-exp"

    async def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY mancante")
        import httpx as _httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
        }
        async with _httpx.AsyncClient(timeout=30.0) as c:
            resp = await c.post(url, json=payload)
            if resp.status_code == 429:
                logger.warning("Gemini: rate limit (60 req/min), fallback template")
                raise RuntimeError("rate_limit")
            if resp.status_code == 403:
                logger.warning("Gemini: API key non valida o regione non supportata")
                raise RuntimeError("invalid_key")
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)


class GroqProvider:
    """Groq API (gratuito: 30 richieste/minuto, velocissimo).

    Prendi API key su https://console.groq.com/keys
    Metti GROQ_API_KEY nel .env
    """

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = "llama-3.3-70b-versatile"

    async def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY mancante")
        import httpx as _httpx
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with _httpx.AsyncClient(timeout=30.0) as c:
            resp = await c.post(url, json=payload, headers=headers)
            if resp.status_code == 429:
                logger.warning("Groq: rate limit (30 req/min), fallback template")
                raise RuntimeError("rate_limit")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


class OpenRouterProvider:
    """OpenRouter gateway 200+ modelli (free tier + $1 credito).

    Prendi API key su https://openrouter.ai/keys
    Metti OPENROUTER_API_KEY nel .env
    Modelli gratuiti: mistralai/mistral-7b-instruct, google/gemma-2-9b-it, ecc.
    """

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model or "mistralai/mistral-7b-instruct:free"

    async def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY mancante")
        import httpx as _httpx
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_referer or "http://localhost:8000",
        }
        async with _httpx.AsyncClient(timeout=30.0) as c:
            resp = await c.post(url, json=payload, headers=headers)
            if resp.status_code == 429:
                logger.warning("OpenRouter: rate limit, fallback template")
                raise RuntimeError("rate_limit")
            resp.raise_for_status()
            choice = resp.json()["choices"][0]
            return choice["message"]["content"]


class LLMEnsemble:
    """Usa il primo LLM disponibile: Gemini → Groq → OpenRouter → template fallback."""

    def __init__(self):
        self.providers = []
        if settings.gemini_api_key:
            self.providers.append(("Gemini", GeminiProvider()))
        if settings.groq_api_key:
            self.providers.append(("Groq", GroqProvider()))
        if settings.openrouter_api_key:
            self.providers.append(("OpenRouter", OpenRouterProvider()))

    async def generate(self, prompt: str, max_tokens: int = 2048) -> str | None:
        for name, provider in self.providers:
            try:
                result = await provider.generate(prompt, max_tokens)
                if result:
                    logger.info(f"LLM: usato {name}")
                    return result
            except RuntimeError:
                continue
            except Exception as e:
                logger.warning(f"LLM {name} errore: {e}")
                continue
        return None
