from __future__ import annotations
import os
from pathlib import Path
from loguru import logger
from app.config import settings


class VideoCompiler:
    async def compile(
        self,
        image_paths: list[str],
        audio_paths: list[str],
        subtitle_path: str | None,
        output_path: str,
        durations: list[float],
    ) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if len(image_paths) != len(audio_paths) or len(image_paths) != len(durations):
            raise ValueError("Mismatch scene/audio/durations count")

        if len(image_paths) == 1:
            return await self._single_scene(image_paths[0], audio_paths[0], output_path, durations[0])
        return await self._multi_scene(image_paths, audio_paths, durations, output_path, subtitle_path)

    async def _single_scene(self, image_path: str, audio_path: str, output_path: str, duration: float) -> str:
        from moviepy import AudioFileClip, ImageClip

        audio = AudioFileClip(audio_path)
        img = ImageClip(image_path, duration=duration)
        img = img.with_duration(duration)
        video = img.with_audio(audio)
        video.write_videofile(output_path, fps=settings.video_fps, codec="libx264", audio_codec="aac", logger=None)
        video.close()
        audio.close()
        logger.info(f"Video singolo: {output_path}")
        return output_path

    async def _multi_scene(
        self, image_paths: list[str], audio_paths: list[str],
        durations: list[float], output_path: str, subtitle_path: str | None,
    ) -> str:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip

        clips = []
        for img_path, aud_path, dur in zip(image_paths, audio_paths, durations):
            audio = AudioFileClip(aud_path)
            actual_dur = min(dur, audio.duration)
            clip = ImageClip(img_path, duration=actual_dur).with_audio(audio)
            clips.append(clip)

        final = concatenate_videoclips(clips, method="compose")

        if subtitle_path and os.path.exists(subtitle_path):
            try:
                from moviepy import TextClip
                subs = self._parse_srt(subtitle_path)
                txt_clips = []
                for start, end, text in subs:
                    try:
                        font_path = str(settings.subtitle_font) if settings.subtitle_font else str(settings.FONTS_DIR / "NotoSans-Regular.ttf")
                        txt = TextClip(text=text, font=font_path, font_size=36, color="white", stroke_color="black", stroke_width=2)
                        txt = txt.with_position(("center", "bottom")).with_duration(end - start).with_start(start)
                        txt_clips.append(txt)
                    except Exception:
                        pass
                if txt_clips:
                    final = CompositeVideoClip([final, *txt_clips])
            except Exception as e:
                logger.warning(f"Errore sottotitoli: {e}")

        final.write_videofile(output_path, fps=settings.video_fps, codec="libx264", audio_codec="aac", logger=None)
        final.close()
        for c in clips:
            c.close()
        logger.info(f"Video multi-scena: {output_path}")
        return output_path

    def _parse_srt(self, srt_path: str) -> list[tuple[float, float, str]]:
        import srt
        subs = []
        with open(srt_path, encoding="utf-8") as f:
            for sub in srt.parse(f.read()):
                subs.append((sub.start.total_seconds(), sub.end.total_seconds(), sub.content))
        return subs
