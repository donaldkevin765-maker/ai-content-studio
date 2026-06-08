from __future__ import annotations
import os
import uuid
from pathlib import Path
from loguru import logger
from app.config import OUTPUT_DIR, AUDIO_DIR, IMAGES_DIR, VIDEOS_DIR
from app.supabase_client import get_supabase_storage


def unique_filename(extension: str = ".mp4") -> str:
    return f"{uuid.uuid4().hex}{extension}"


def video_output_path(filename: str | None = None) -> str:
    return str(VIDEOS_DIR / (filename or unique_filename(".mp4")))


def audio_output_path(filename: str | None = None) -> str:
    return str(AUDIO_DIR / (filename or unique_filename(".mp3")))


def image_output_path(filename: str | None = None) -> str:
    return str(IMAGES_DIR / (filename or unique_filename(".png")))


async def cleanup_scene_files(image_path: str, audio_path: str):
    storage = get_supabase_storage()
    for p in [image_path, audio_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except OSError as e:
                logger.warning(f"Impossibile rimuovere {p}: {e}")


async def cleanup_video_files(video_id: int, image_paths: list[str], audio_paths: list[str], video_path: str):
    storage = get_supabase_storage()
    for p in image_paths + audio_paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    if video_path and os.path.exists(video_path):
        try:
            os.remove(video_path)
        except OSError:
            pass
    await storage.delete_file(f"videos/video_{video_id}.mp4")
    await storage.delete_file(f"videos/video_{video_id}_subtitles.srt")
