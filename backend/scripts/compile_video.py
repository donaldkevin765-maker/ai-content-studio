#!/usr/bin/env python3
"""Scarica gli assets da Supabase Storage e compila il video finale con ffmpeg.

Usage:
    python scripts/compile_video.py <video_id>
    
Esempio:
    python scripts/compile_video.py 8
    
Richiede:
    - pip install httpx imageio-ffmpeg moviepy
    - ffmpeg (o imageio-ffmpeg provvede ffmpeg statico)
"""

import argparse
import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Optional

# Aggiungi la directory root al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import DBContext, sql
from app.services.video_compiler import VideoCompiler
from app.services.subtitle_generator import SubtitleGenerator
from app.utils.file_utils import audio_output_path, image_output_path, video_output_path

SUPABASE_URL = settings.supabase_url or "https://endxgujdxrzssccfikql.supabase.co"
BUCKET = settings.supabase_bucket or "videos"


async def download_asset(remote_path: str, local_path: str) -> Optional[str]:
    """Scarica un file da Supabase Storage."""
    import httpx
    url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{remote_path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        if resp.is_success:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(resp.content)
            print(f"  ✓ Scaricato: {local_path}")
            return local_path
        print(f"  ✗ Errore download {url}: HTTP {resp.status_code}")
        return None


async def compile_video(video_id: int):
    print(f"\n=== Compilazione video {video_id} ===\n")

    # Ottieni le scene dal database via Management API
    async with DBContext() as db:
        video = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
        if not video:
            print(f"❌ Video {video_id} non trovato")
            return

        print(f"Titolo: {video['title']}")
        print(f"Stato: {video['status']}")

        scenes = await db.fetch_all(
            sql('SELECT * FROM scenes WHERE video_id = :vid ORDER BY "order"', vid=video_id)
        )
        if not scenes:
            print(f"❌ Nessuna scena per video {video_id}")
            return

        print(f"Scene: {len(scenes)}")
        durations = [float(s["duration"]) for s in scenes]
        scene_texts = [s["content"] for s in scenes]

        print(f"Durata totale: {sum(durations)}s")
        print()

        # Crea le directory di output
        output_dir = Path(f"./output/videos")
        audio_dir = Path(f"./output/audio")
        images_dir = Path(f"./output/images")
        for d in [output_dir, audio_dir, images_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Scarica gli assets
        print("Scaricamento assets...")
        audio_paths = []
        image_paths = []
        for i in range(len(scenes)):
            aud_local = audio_dir / f"scene_{video_id}_{i}.mp3"
            img_local = images_dir / f"scene_{video_id}_{i}.png"
            aud = await download_asset(f"assets/{video_id}/audio_{i}.mp3", str(aud_local))
            img = await download_asset(f"assets/{video_id}/image_{i}.png", str(img_local))
            if aud and img:
                audio_paths.append(aud)
                image_paths.append(img)

        srt_local = output_dir / f"subtitles_{video_id}.srt"
        srt = await download_asset(f"assets/{video_id}/subtitles.srt", str(srt_local))
        srt_path = str(srt_local) if srt else None

        if not audio_paths or not image_paths:
            print("❌ Assets insufficienti per la compilazione")
            return

        # Genera subtitles se mancanti
        if not srt:
            print("Generazione sottotitoli locale...")
            sub_gen = SubtitleGenerator()
            srt_path = str(srt_local)
            sub_gen.generate_srt(scene_texts, durations, srt_path)

        # Compila il video
        print("\nCompilazione video con ffmpeg...")
        output_path = str(output_dir / f"video_{video_id}.mp4")
        compiler = VideoCompiler()
        try:
            await compiler.compile(image_paths, audio_paths, srt_path, output_path, durations)
        except Exception as e:
            print(f"❌ Errore compilazione: {e}")
            return

        # Upload del video finito
        print("\nUpload video finito a Supabase Storage...")
        from app.supabase_client import get_supabase_storage
        storage = get_supabase_storage()
        supabase_url = await storage.upload_file(output_path, f"videos/video_{video_id}.mp4")

        # Aggiorna lo stato del video
        print("Aggiornamento stato video...")
        if supabase_url:
            await db.execute(
                sql("""UPDATE videos SET status = 'completed',
                       output_path = :opath, output_url = :ourl,
                       duration = :dur, progress_percent = 100.0, progress_step = 'Completato'
                       WHERE id = :id""",
                    opath=output_path, ourl=str(supabase_url),
                    dur=sum(durations), id=video_id)
            )
            print(f"\n✅ Video completato!")
            print(f"   URL: {supabase_url}")
        else:
            print(f"\n⚠️ Video compilato ma upload fallito")
            print(f"   File locale: {output_path}")

        # Pulisci gli assets scaricati
        print("\nPulizia files temporanei...")
        for p in audio_paths + image_paths:
            try:
                os.remove(p)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description="Compila video da assets su Supabase")
    parser.add_argument("video_id", type=int, help="ID del video da compilare")
    args = parser.parse_args()

    asyncio.run(compile_video(args.video_id))


if __name__ == "__main__":
    main()
