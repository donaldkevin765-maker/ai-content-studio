from __future__ import annotations

import pytest
from app.services.webhook import WebhookService


class TestWebhookService:
    def setup_method(self):
        self.service = WebhookService()

    @pytest.mark.asyncio
    async def test_no_op_when_no_url(self):
        await self.service.notify("test.event", {"key": "value"})
        # Non deve lanciare eccezioni

    @pytest.mark.asyncio
    async def test_video_completed_no_url(self):
        await self.service.video_completed(1, "http://example.com", 30.0)
