from __future__ import annotations
import asyncio
import os
from pathlib import Path
from loguru import logger

from app.workers.celery_app import celery_app, _celery_available
from app.database import DBContext, sql
from app.services.text_to_speech import TextToSpeechService
from app.services.image_generator import ImageGenerator
from app.services.video_compiler import VideoCompiler
from app.services.subtitle_generator import SubtitleGenerator
from app.services.webhook import WebhookService
from app.services.progress import progress_tracker
from app.services.notion_integration import NotionService
from app.utils.file_utils import audio_output_path, image_output_path, video_output_path
from app.supabase_client import get_supabase_storage


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Se Celery è disponibile, registra il task decorato
if _celery_available and celery_app is not None:
    @celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
    def generate_video_task(self, video_id: int):
        logger.info(f"Avvio generazione video {video_id}")
        run_async(_generate_video(video_id, self))
else:
    # Fallback: funzione normale senza Celery
    def generate_video_task(self=None, video_id=None):
        logger.info(f"Avvio generazione video {video_id} (senza Celery)")
        if video_id is not None:
            run_async(_generate_video(video_id, self or object()))


async def _generate_video(video_id: int, task):
    tts = TextToSpeechService()
    img_gen = ImageGenerator()
    compiler = VideoCompiler()
    sub_gen = SubtitleGenerator()
    webhook = WebhookService()
    notion = NotionService()

    async with DBContext() as db:
        video = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
        if not video:
            logger.error(f"Video {video_id} non trovato")
            return

        scenes = await db.fetch_all(
            sql('SELECT * FROM scenes WHERE video_id = :vid ORDER BY "order"', vid=video_id)
        )

        if not scenes:
            logger.error(f"Nessuna scena per video {video_id}")
            await db.execute(
                sql("UPDATE videos SET status = 'error', error_message = 'Nessuna scena trovata' WHERE id = :id",
                    id=video_id)
            )
            await webhook.video_error(video_id, "Nessuna scena trovata")
            return

        try:
            await webhook.n8n_trigger("video-start", {
                "video_id": video_id,
                "title": video.get("title", ""),
            })
        except Exception:
            pass

        try:
            project_title = video.get("title", "Video AI") or "Video AI"
            await notion.create_video_project(project_title, f"Video #{video_id}", video.get("script", "") or "")
        except Exception:
            pass

        progress_tracker.start(video_id, len(scenes))

        try:
            scene_count = len(scenes)
            durations = [float(s["duration"]) for s in scenes]
            scene_texts = [s["content"] for s in scenes]

            # Update DB only at start
            await db.execute(
                sql("UPDATE videos SET progress_percent = 5.0, progress_step = 'Generazione audio e immagini' WHERE id = :id",
                    id=video_id)
            )

            # Genera audio e immagini in parallelo per tutte le scene
            async def gen_scene(i: int, scene: dict) -> tuple[str, str]:
                content = scene["content"]
                img_prompt = scene.get("image_prompt", "") or content
                aud_path = audio_output_path(f"scene_{video_id}_{i}.mp3")
                img_path = image_output_path(f"scene_{video_id}_{i}.png")
                await asyncio.gather(
                    tts.generate(content, aud_path),
                    img_gen.generate(img_prompt, img_path),
                )
                return aud_path, img_path

            results = await asyncio.gather(*[gen_scene(i, s) for i, s in enumerate(scenes)])
            audio_paths = [r[0] for r in results]
            image_paths = [r[1] for r in results]

            progress_tracker.update(video_id, scene_count, "Generazione sottotitoli")
            await db.execute(
                sql("UPDATE videos SET progress_percent = 80.0, progress_step = 'Sottotitoli' WHERE id = :id",
                    id=video_id)
            )

            srt_path = str(Path(video_output_path()).parent / f"subtitles_{video_id}.srt")
            sub_gen.generate_srt(scene_texts, durations, srt_path)

            progress_tracker.update(video_id, len(scenes), "Caricamento assets su cloud")
            await db.execute(
                sql("UPDATE videos SET progress_percent = 90.0, progress_step = 'Caricamento assets' WHERE id = :id",
                    id=video_id)
            )

            # Upload individual assets to Supabase Storage (skip moviepy compilation on serverless)
            storage = get_supabase_storage()
            for i, (aud_path, img_path) in enumerate(zip(audio_paths, image_paths)):
                await storage.upload_file(aud_path, f"assets/{video_id}/audio_{i}.mp3")
                await storage.upload_file(img_path, f"assets/{video_id}/image_{i}.png")
            await storage.upload_file(srt_path, f"assets/{video_id}/subtitles.srt")

            # Try video compilation; if it fails (timeout / no ffmpeg), assets are already saved
            try:
                await db.execute(
                    sql("UPDATE videos SET progress_percent = 95.0, progress_step = 'Rendering video' WHERE id = :id",
                        id=video_id)
                )
                output_path = video_output_path(f"video_{video_id}.mp4")
                await compiler.compile(image_paths, audio_paths, srt_path, output_path, durations, fast=True)
                supabase_url = await storage.upload_file(output_path, f"videos/video_{video_id}.mp4")

                await db.execute(
                    sql("""UPDATE videos SET status = 'completed',
                           output_path = :opath, output_url = :ourl,
                           duration = :dur, progress_percent = 100.0, progress_step = 'Completato'
                           WHERE id = :id""",
                        opath=output_path, ourl=str(supabase_url or output_path),
                        dur=sum(durations), id=video_id)
                )
                progress_tracker.finish(video_id)
                await webhook.video_completed(video_id, str(supabase_url or output_path), sum(durations))
                logger.info(f"Video {video_id} completato con rendering")
            except Exception as compile_err:
                # Assets saved, but video compilation failed — mark as assets_ready
                logger.warning(f"Compilazione video {video_id} fallita ({compile_err}), assets salvati su cloud")
                await db.execute(
                    sql("""UPDATE videos SET status = 'assets_ready',
                           duration = :dur, progress_percent = 90.0, progress_step = 'Assets pronti, compila localmente'
                           WHERE id = :id""",
                        dur=sum(durations), id=video_id)
                )
                progress_tracker.finish(video_id)

        except Exception as e:
            logger.error(f"Errore video {video_id}: {e}")
            progress_tracker.fail(video_id, str(e))
            await db.execute(
                sql("""UPDATE videos SET status = 'error', error_message = :err,
                       progress_step = :step WHERE id = :id""",
                    err=str(e), step=f"Errore: {e}", id=video_id)
            )
            await webhook.video_error(video_id, str(e))
            raise


async def _compile_assets(video_id: int):
    """Step di compilazione standalone: scarica asset da Supabase, compila con ffmpeg, carica il video finito."""
    from pathlib import Path
    import tempfile

    compiler = VideoCompiler()
    sub_gen = SubtitleGenerator()
    storage = get_supabase_storage()

    async with DBContext() as db:
        video = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
        if not video:
            logger.error(f"Video {video_id} non trovato")
            return

        scenes = await db.fetch_all(
            sql('SELECT * FROM scenes WHERE video_id = :vid ORDER BY "order"', vid=video_id)
        )
        if not scenes:
            logger.error(f"Nessuna scena per video {video_id}")
            return

        durations = [float(s["duration"]) for s in scenes]
        scene_texts = [s["content"] for s in scenes]

        await db.execute(
            sql("UPDATE videos SET progress_percent = 50.0, progress_step = 'Scaricamento assets' WHERE id = :id",
                id=video_id)
        )

        # Scarica gli asset da Supabase in una directory temporanea
        with tempfile.TemporaryDirectory(prefix=f"compile_{video_id}_") as tmpdir:
            audio_paths = []
            image_paths = []
            for i in range(len(scenes)):
                aud = await storage.download_file(f"assets/{video_id}/audio_{i}.mp3",
                                                   str(Path(tmpdir) / f"audio_{i}.mp3"))
                img = await storage.download_file(f"assets/{video_id}/image_{i}.png",
                                                   str(Path(tmpdir) / f"image_{i}.png"))
                if aud:
                    audio_paths.append(aud)
                if img:
                    image_paths.append(img)

            srt_local = str(Path(tmpdir) / "subtitles.srt")
            srt_path = await storage.download_file(f"assets/{video_id}/subtitles.srt", srt_local)

            if not audio_paths or not image_paths:
                logger.error(f"Asset insufficienti per compilazione video {video_id}")
                await db.execute(
                    sql("UPDATE videos SET status = 'error', error_message = 'Asset mancanti' WHERE id = :id",
                        id=video_id)
                )
                return

            # Genera SRT se non disponibile
            if not srt_path:
                srt_path = srt_local
                sub_gen.generate_srt(scene_texts, durations, srt_path)

            await db.execute(
                sql("UPDATE videos SET progress_percent = 75.0, progress_step = 'Compilazione video con ffmpeg' WHERE id = :id",
                    id=video_id)
            )

            # Compila
            output_path = str(Path(tmpdir) / f"video_{video_id}.mp4")
            try:
                await compiler.compile(image_paths, audio_paths, srt_path, output_path, durations, fast=True)
            except Exception as e:
                logger.error(f"Compilazione ffmpeg fallita: {e}")
                await db.execute(
                    sql("UPDATE videos SET status = 'error', error_message = :err, progress_step = :step WHERE id = :id",
                        err=str(e), step=f"Errore ffmpeg: {e}", id=video_id)
                )
                return

            # Upload video finito
            await db.execute(
                sql("UPDATE videos SET progress_percent = 95.0, progress_step = 'Upload video finito' WHERE id = :id",
                    id=video_id)
            )

            supabase_url = await storage.upload_file(output_path, f"videos/video_{video_id}.mp4")

            await db.execute(
                sql("""UPDATE videos SET status = 'completed',
                       output_path = :opath, output_url = :ourl,
                       duration = :dur, progress_percent = 100.0, progress_step = 'Completato'
                       WHERE id = :id""",
                    opath=output_path, ourl=str(supabase_url or output_path),
                    dur=sum(durations), id=video_id)
            )

            logger.info(f"Video {video_id} compilato e caricato: {supabase_url}")


# Task di pulizia (solo se Celery disponibile)
if _celery_available and celery_app is not None:
    @celery_app.task
    def cleanup_old_outputs():
        _do_cleanup()
else:
    def cleanup_old_outputs():
        _do_cleanup()


def _do_cleanup():
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
