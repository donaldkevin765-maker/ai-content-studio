from __future__ import annotations

import pytest
from app.services.translator import TranslatorService


class TestTranslatorService:
    def setup_method(self):
        self.service = TranslatorService()

    @pytest.mark.asyncio
    async def test_same_language_passthrough(self):
        result = await self.service.translate("Ciao", "it")
        assert result == "Ciao"

    @pytest.mark.asyncio
    async def test_returns_text_when_no_llm(self):
        result = await self.service.translate("Hello world", "it")
        assert isinstance(result, str)
