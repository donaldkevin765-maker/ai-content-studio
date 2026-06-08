from __future__ import annotations

import pytest
import tempfile
import os
from app.services.subtitle_generator import SubtitleGenerator


class TestSubtitleGenerator:
    def setup_method(self):
        self.gen = SubtitleGenerator()

    def test_generates_srt_file(self):
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
            out = f.name
        try:
            scenes = ["Ciao mondo", "Test"]
            durations = [5.0, 3.0]
            result = self.gen.generate_srt(scenes, durations, out)

            assert os.path.exists(out)
            with open(out, encoding="utf-8") as f:
                content = f.read()

            assert "1" in content
            assert "2" in content
            assert "Ciao mondo" in content
            assert "-->" in content
        finally:
            os.unlink(out)

    def test_timing_format(self):
        formatted = self.gen._format_time(3661.5)
        assert "-->" not in formatted
        assert "," in formatted

    def test_empty_srt(self):
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
            out = f.name
        try:
            self.gen.generate_srt([], [], out)
            with open(out, encoding="utf-8") as f:
                content = f.read()
            assert content.strip() == ""
        finally:
            os.unlink(out)
