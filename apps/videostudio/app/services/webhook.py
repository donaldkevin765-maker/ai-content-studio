from __future__ import annotations
import hashlib
import hmac
import httpx
from loguru import logger
from app.config import settings


class WebhookService:
    def __init__(self):
        self.url = settings.webhook_url
        self.secret = settings.webhook_secret

    async def notify(self, event: str, payload: dict):
        if not self.url:
            return

        data = {"event": event, **payload}
        headers = {"Content-Type": "application/json"}

        if self.secret:
            import json
            body = json.dumps(data, sort_keys=True)
            signature = hmac.new(self.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = signature

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.url, json=data, headers=headers)
                logger.info(f"Webhook {event} inviato: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Errore webhook {event}: {e}")

    async def video_completed(self, video_id: int, output_url: str, duration: float):
        await self.notify("video.completed", {
            "video_id": video_id,
            "output_url": output_url,
            "duration": duration,
        })

    async def video_error(self, video_id: int, error: str):
        await self.notify("video.error", {
            "video_id": video_id,
            "error": error,
        })

    async def video_progress(self, video_id: int, percent: float, step: str):
        await self.notify("video.progress", {
            "video_id": video_id,
            "percent": percent,
            "step": step,
        })

    async def n8n_trigger(self, workflow_id: str, payload: dict):
        """Triggera un workflow n8n self-hostato.

        Configura WEBHOOK_URL = http://localhost:5678/webhook/<workflow_id>
        n8n è open source e gratuito: docker run -it --rm -p 5678:5678 n8nio/n8n
        """
        url = getattr(settings, 'n8n_webhook_url', None) or self.url
        if not url:
            logger.warning("n8n: WEBHOOK_URL non configurata")
            return
        await self.notify(f"n8n.{workflow_id}", payload)
