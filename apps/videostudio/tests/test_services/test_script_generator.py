from __future__ import annotations

import pytest
from app.services.script_generator import ScriptGenerator


class TestScriptGenerator:
    def setup_method(self):
        self.gen = ScriptGenerator()

    @pytest.mark.asyncio
    async def test_generates_script_with_scenes(self):
        result = await self.gen.generate(topic="intelligenza artificiale", duration_sec=60, style="informativo")
        assert "full_script" in result
        assert "scenes" in result
        assert len(result["scenes"]) >= 2
        assert len(result["full_script"]) > 50

    @pytest.mark.asyncio
    async def test_all_styles(self):
        for style in ["informativo", "divertente", "didattico", "motivazionale", "serio"]:
            result = await self.gen.generate(topic="AI", duration_sec=30, style=style)
            assert len(result["scenes"]) > 0, f"Stile {style} fallito"

    @pytest.mark.asyncio
    async def test_scene_fields(self):
        result = await self.gen.generate(topic="Python", duration_sec=30)
        for scene in result["scenes"]:
            assert "content" in scene
            assert "image_prompt" in scene
            assert "duration" in scene

    @pytest.mark.asyncio
    async def test_duration_affects_scenes(self):
        short = await self.gen.generate(topic="AI", duration_sec=20)
        long = await self.gen.generate(topic="AI", duration_sec=120)
        assert len(short["scenes"]) <= len(long["scenes"])

    @pytest.mark.asyncio
    async def test_custom_topic(self):
        result = await self.gen.generate(topic="fotografia digitale", duration_sec=45, style="didattico")
        assert len(result["scenes"]) > 0
        assert "fotografia" in result["full_script"].lower() or "fotografia" in result["full_script"]
