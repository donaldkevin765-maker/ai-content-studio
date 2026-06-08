from __future__ import annotations
import asyncio
import os
from pathlib import Path
from loguru import logger

from app.workers.celery_app import celery_app
from app.database import get_session_factory
from app.models.video import Video
from app.models.scene import Scene
from app.services.text_to_speech import TextToSpeechService
from app.services.image_generator import ImageGenerator
from app.services.video_compiler import VideoCompiler
from app.services.subtitle_generator import SubtitleGenerator
from app.services.webhook import WebhookService
from app.services.progress import progress_tracker
from app.services.notion_integration import NotionService
from app.utils.file_utils import audio_output_path, image_output_path, video_output_path
from app.supabase_client import get_supabase_storage
from sqlalchemy import select


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_video_task(self, video_id: int):
    logger.info(f"Avvio generazione video {video_id}")
    run_async(_generate_video(video_id, self))


async def _generate_video(video_id: int, task):
    tts = TextToSpeechService()
    img_gen = ImageGenerator()
    compiler = VideoCompiler()
    sub_gen = SubtitleGenerator()
    webhook = WebhookService()
    notion = NotionService()

    async with get_session_factory()() as db:
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            logger.error(f"Video {video_id} non trovato")
            return

        scenes_q = await db.execute(
            select(Scene).where(Scene.video_id == video_id).order_by(Scene.order)
        )
        scenes = scenes_q.scalars().all()

        if not scenes:
            logger.error(f"Nessuna scena per video {video_id}")
            video.status = "error"
            video.error_message = "Nessuna scena trovata"
            await db.commit()
            await webhook.video_error(video_id, "Nessuna scena trovata")
            return

        try:
            await webhook.n8n_trigger("video-start", {
                "video_id": video_id,
                "title": video.title or "",
            })
        except Exception:
            pass

        try:
            project_title = getattr(video, 'title', 'Video AI') or 'Video AI'
            await notion.create_video_project(project_title, f"Video #{video_id}", video.script or "")
        except Exception:
            pass

        progress_tracker.start(video_id, len(scenes))

        try:
            image_paths = []
            audio_paths = []
            durations = []
            scene_texts = []

            for i, scene in enumerate(scenes):
                content = scene.content
                img_prompt = scene.image_prompt or content
                scene_texts.append(content)

                progress_tracker.update(video_id, i + 1, "Generazione audio TTS")
                video.progress_percent = round(((i + 0.3) / len(scenes)) * 100, 1)
                video.progress_step = f"Audio scena {i + 1}/{len(scenes)}"
                await db.commit()

                aud_path = audio_output_path(f"scene_{video_id}_{i}.mp3")
                await tts.generate(content, aud_path)
                audio_paths.append(aud_path)

                progress_tracker.update(video_id, i + 1, "Generazione immagine")
                video.progress_percent = round(((i + 0.6) / len(scenes)) * 100, 1)
                video.progress_step = f"Immagine scena {i + 1}/{len(scenes)}"
                await db.commit()

                img_path = image_output_path(f"scene_{video_id}_{i}.png")
                await img_gen.generate(img_prompt, img_path)
                image_paths.append(img_path)

                durations.append(float(scene.duration))

            progress_tracker.update(video_id, len(scenes), "Generazione sottotitoli")
            video.progress_percent = 90.0
            video.progress_step = "Sottotitoli"
            await db.commit()

            srt_path = str(Path(video_output_path()).parent / f"subtitles_{video_id}.srt")
            sub_gen.generate_srt(scene_texts, durations, srt_path)

            progress_tracker.update(video_id, len(scenes), "Compilazione video")
            video.progress_percent = 95.0
            video.progress_step = "Rendering video"
            await db.commit()

            output_path = video_output_path(f"video_{video_id}.mp4")
            await compiler.compile(image_paths, audio_paths, srt_path, output_path, durations)

            storage = get_supabase_storage()
            supabase_url = await storage.upload_file(output_path, f"videos/video_{video_id}.mp4")

            video.status = "completed"
            video.output_path = output_path
            video.output_url = supabase_url or output_path
            video.duration = sum(durations)
            video.progress_percent = 100.0
            video.progress_step = "Completato"
            await db.commit()

            progress_tracker.finish(video_id)
            await webhook.video_completed(video_id, video.output_url, video.duration)
            logger.info(f"Video {video_id} completato")

        except Exception as e:
            logger.error(f"Errore video {video_id}: {e}")
            progress_tracker.fail(video_id, str(e))
            video.status = "error"
            video.error_message = str(e)
            video.progress_step = f"Errore: {e}"
            await db.commit()
            await webhook.video_error(video_id, str(e))
            raise


@celery_app.task
def cleanup_old_outputs():
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=7)
    for subdir in ["videos", "audio", "images"]:
        target = Path(f"./output/{subdir}")
        if not target.exists():
            continue
        for f in target.iterdir():
            if f.is_file() and f.suffix in {".mp4", ".mp3", ".wav", ".png", ".jpg", ".srt"}:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    logger.info(f"Pulito: {f}")
