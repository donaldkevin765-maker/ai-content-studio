from __future__ import annotations
import datetime
from pathlib import Path
from loguru import logger


class SubtitleGenerator:
    def generate_srt(self, scenes_text: list[str], audio_durations: list[float], output_path: str) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        subs = []
        current_time = 0.0

        for i, (text, dur) in enumerate(zip(scenes_text, audio_durations)):
            start = current_time
            end = current_time + dur
            subs.append(self._make_subtitle(i + 1, start, end, text))
            current_time = end

        content = "\n\n".join(subs)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"SRT generato: {output_path}")
        return output_path

    def _make_subtitle(self, index: int, start_sec: float, end_sec: float, text: str) -> str:
        return f"{index}\n{self._format_time(start_sec)} --> {self._format_time(end_sec)}\n{text}"

    def _format_time(self, seconds: float) -> str:
        total = int(seconds)
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
