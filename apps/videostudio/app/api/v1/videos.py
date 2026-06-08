from __future__ import annotations
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.project import Project
from app.models.video import Video
from app.models.scene import Scene
from app.schemas.video import (
    VideoCreate, VideoResponse, VideoDetailResponse,
    GenerateScriptRequest, GenerateScriptResponse, PaginatedVideoResponse,
)
from app.schemas.scene import SceneResponse
from app.schemas.progress import ProgressResponse
from app.services.script_generator import ScriptGenerator
from app.services.translator import TranslatorService
from app.workers.tasks import generate_video_task
from app.services.progress import progress_tracker
from app.supabase_client import get_supabase_storage
from app.auth import require_auth

router = APIRouter()


@router.get("/", response_model=PaginatedVideoResponse)
async def list_videos(
    project_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(require_auth),
):
    query = select(Video)
    count_query = select(sql_func.count(Video.id))
    if project_id is not None:
        query = query.where(Video.project_id == project_id)
        count_query = count_query.where(Video.project_id == project_id)

    total_q = await db.execute(count_query)
    total = total_q.scalar() or 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    result = await db.execute(query.offset(offset).limit(page_size).order_by(Video.created_at.desc()))
    items = result.scalars().all()

    return PaginatedVideoResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.post("/", response_model=VideoResponse, status_code=201)
async def create_video(data: VideoCreate, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    proj_q = await db.execute(select(Project.id).where(Project.id == data.project_id))
    if not proj_q.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    video = Video(project_id=data.project_id, title=data.title)
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    result = await db.execute(select(Video).options(selectinload(Video.scenes)).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video non trovato")
    return video


@router.get("/{video_id}/scenes", response_model=list[SceneResponse])
async def list_scenes(video_id: int, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    vid_q = await db.execute(select(Video.id).where(Video.id == video_id))
    if not vid_q.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Video non trovato")
    result = await db.execute(select(Scene).where(Scene.video_id == video_id).order_by(Scene.order))
    return result.scalars().all()


@router.get("/{video_id}/progress", response_model=ProgressResponse)
async def get_progress(video_id: int):
    prog = progress_tracker.get(video_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Nessun progresso attivo")
    return prog


@router.post("/{video_id}/generate-script", response_model=GenerateScriptResponse)
async def generate_script(
    video_id: int, req: GenerateScriptRequest,
    db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth),
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video non trovato")

    generator = ScriptGenerator()
    script_data = await generator.generate(topic=req.topic, duration_sec=req.duration_seconds, style=req.style)

    if req.target_language and req.target_language != db.bind.dialect.name:
        translator = TranslatorService()
        for scene in script_data["scenes"]:
            scene["content"] = await translator.translate(scene["content"], req.target_language)
            scene["subtitle_text"] = scene["content"]
        script_data["full_script"] = "\n\n".join(s["content"] for s in script_data["scenes"])

    video.script = script_data["full_script"]
    video.status = "script_ready"

    for i, s in enumerate(script_data["scenes"]):
        db.add(Scene(
            video_id=video_id, order=i, content=s["content"],
            image_prompt=s.get("image_prompt", ""),
            subtitle_text=s.get("subtitle_text", s["content"]),
            duration=s.get("duration", 5.0),
        ))

    await db.commit()
    await db.refresh(video)
    return GenerateScriptResponse(video_id=video.id, script=video.script, scenes=script_data["scenes"])


@router.post("/{video_id}/render", response_model=VideoResponse)
async def render_video(video_id: int, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video non trovato")
    if video.status not in ("script_ready", "error"):
        raise HTTPException(status_code=400, detail=f"Video in stato '{video.status}', non renderizzabile. Genera prima lo script.")

    video.status = "rendering"
    await db.commit()
    try:
        generate_video_task.apply_async(args=[video_id], ignore_result=True)
    except Exception as e:
        logger.warning(f"Celery/Redis non disponibile ({type(e).__name__}), avvio rendering inline: {e}")
        import asyncio
        try:
            from app.workers.tasks import _generate_video

            class _Stub:
                def update_state(self, *a, **kw): pass
                request = type("R", (), {})()

            asyncio.create_task(_generate_video(video_id, _Stub()))
        except Exception as e2:
            logger.error(f"Fallback inline fallito: {e2}")
    await db.refresh(video)
    return video


@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: int, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video non trovato")

    storage = get_supabase_storage()
    if video.output_url:
        remote = f"videos/video_{video_id}.mp4"
        await storage.delete_file(remote)

    await db.delete(video)
    await db.commit()
