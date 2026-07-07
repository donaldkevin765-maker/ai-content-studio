from __future__ import annotations
from typing import Optional
import asyncio
import os
import subprocess
from pathlib import Path
from loguru import logger
from app.config import settings


def _ensure_ffmpeg():
    """Make sure ffmpeg is available.

    On Vercel serverless ffmpeg is NOT available.
    Use the GitHub Actions workflow for compilation:
    https://github.com/donaldkevin765-maker/ai-content-studio/actions
    """
    # 1. Check imageio-ffmpeg (bundled during pip install)
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg = get_ffmpeg_exe()
        if ffmpeg and Path(ffmpeg).exists():
            os.environ["FFMPEG_BINARY"] = ffmpeg
            os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg
            logger.info(f"ffmpeg (imageio): {ffmpeg}")
            return ffmpeg
    except Exception as e:
        logger.warning(f"imageio-ffmpeg: {e}")

    # 2. Check FFMPEG_BINARY env var
    env_path = os.environ.get("FFMPEG_BINARY")
    if env_path and Path(env_path).exists():
        logger.info(f"ffmpeg (env): {env_path}")
        return env_path

    # 3. Check system ffmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            logger.info("ffmpeg (system)")
            return "ffmpeg"
    except Exception:
        pass

    # 4. Check /tmp for manually downloaded ffmpeg (local or CI)
    for p in ["/tmp/ffmpeg/ffmpeg", "/tmp/ffmpeg"]:
        candidate = Path(p)
        if candidate.exists() and candidate.is_file():
            fp = str(candidate.resolve())
            os.environ["FFMPEG_BINARY"] = fp
            logger.info(f"ffmpeg (cached): {fp}")
            return fp

    raise RuntimeError(
        "ffmpeg non disponibile nell'ambiente serverless. "
        "Gli asset sono su Supabase Storage. "
        "Usa il workflow GitHub Actions per compilare il video: "
        ".github/workflows/compile-video.yml"
    )


class VideoCompiler:
    async def compile(
        self,
        image_paths: list[str],
        audio_paths: list[str],
        subtitle_path: Optional[str],
        output_path: str,
        durations: list[float],
        fast: bool = False,
    ) -> str:
        _ensure_ffmpeg()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if len(image_paths) != len(audio_paths) or len(image_paths) != len(durations):
            raise ValueError("Mismatch scene/audio/durations count")

        if fast:
            return await self._compile_fast(image_paths, audio_paths, durations, output_path, subtitle_path)
        if len(image_paths) == 1:
            return await self._single_scene(image_paths[0], audio_paths[0], output_path, durations[0])
        return await self._multi_scene(image_paths, audio_paths, durations, output_path, subtitle_path)

    async def _compile_fast(
        self,
        image_paths: list[str],
        audio_paths: list[str],
        durations: list[float],
        output_path: str,
        subtitle_path: Optional[str],
    ) -> str:
        """Compilazione veloce usando ffmpeg direttamente via subprocess (ultrafast preset)."""
        ffmpeg = _ensure_ffmpeg()

        # Crea un file di concat per l'input
        import tempfile, os
        concat_lines = []
        for img_path, aud_path, dur in zip(image_paths, audio_paths, durations):
            concat_lines.append(f"file '{Path(img_path).resolve()}'\n")
            concat_lines.append(f"duration {dur}\n")
        # Ultimo frame mantenuto per la durata dell'audio finale
        concat_lines.append(f"file '{Path(image_paths[-1]).resolve()}'\n")

        concat_file = str(Path(output_path).parent / "concat.txt")
        with open(concat_file, "w") as f:
            f.writelines(concat_lines)

        cmd = [
            ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
        ]

        # Mixer audio per ogni scena
        filter_parts = []
        for i, (aud_path, dur) in enumerate(zip(audio_paths, durations)):
            filter_parts.append(f"[{i}:a]adelay={int(dur*1000)}|{int(dur*1000)}[a{i}]")

        # Mux audio con filter_complex e amix
        cmd.extend([
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        ])
        for aud_path in audio_paths:
            cmd.extend(["-i", aud_path])

        # Costruisci filter_complex per mixare tutti gli audio
        audio_inputs = "".join(f"[{i+1}:a]" for i in range(len(audio_paths)))
        amix_inputs = "".join(f"[a{i}]" for i in range(len(audio_paths)))
        filter_str = (
            "; ".join(
                f"[{i+1}:a]adelay={int(sum(durations[:i])*1000)}|{int(sum(durations[:i])*1000)}[a{i}]"
                for i in range(len(audio_paths))
            )
            + f"; {amix_inputs}amix=inputs={len(audio_paths)}:duration=first[aout]"
        )

        cmd.extend([
            "-filter_complex", filter_str,
            "-map", "0:v:0",
            "-map", "[aout]",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            output_path,
        ])

        logger.info(f"ffmpeg veloce: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45.0)

        if proc.returncode != 0:
            err = stderr.decode()[:500] if stderr else "unknown error"
            raise RuntimeError(f"ffmpeg fallito (codice {proc.returncode}): {err}")

        logger.info(f"Video compilato veloce: {output_path}")
        return output_path

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
        durations: list[float], output_path: str, subtitle_path: Optional[str],
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
