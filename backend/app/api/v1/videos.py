from __future__ import annotations
from typing import Optional
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import DB, get_db, sql
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
    project_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: DB = Depends(get_db),
    _user: str = Depends(require_auth),
):
    where = ""
    if project_id is not None:
        where = sql(" WHERE project_id = :pid", pid=project_id)

    total_row = await db.fetch_one(f"SELECT COUNT(*) as cnt FROM videos{where}")
    total = total_row["cnt"] if total_row else 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    rows = await db.fetch_all(
        f"SELECT * FROM videos{where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}"
    )

    return PaginatedVideoResponse(
        items=[VideoResponse(**r) for r in rows],
        total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.post("/", response_model=VideoResponse, status_code=201)
async def create_video(data: VideoCreate, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    proj = await db.fetch_one(sql("SELECT id FROM projects WHERE id = :id", id=data.project_id))
    if not proj:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    row = await db.fetch_one(
        sql("INSERT INTO videos (project_id, title) VALUES (:pid, :title) RETURNING *",
            pid=data.project_id, title=data.title)
    )
    if not row:
        raise HTTPException(status_code=500, detail="Creazione video fallita")
    return VideoResponse(**row)


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(video_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    video_row = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
    if not video_row:
        raise HTTPException(status_code=404, detail="Video non trovato")

    scenes = await db.fetch_all(
        sql('SELECT * FROM scenes WHERE video_id = :vid ORDER BY "order"', vid=video_id)
    )
    scene_responses = [SceneResponse(**s) for s in scenes]

    return VideoDetailResponse(**video_row, scenes=scene_responses)


@router.get("/{video_id}/scenes", response_model=list[SceneResponse])
async def list_scenes(video_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    vid = await db.fetch_one(sql("SELECT id FROM videos WHERE id = :id", id=video_id))
    if not vid:
        raise HTTPException(status_code=404, detail="Video non trovato")

    rows = await db.fetch_all(
        sql('SELECT * FROM scenes WHERE video_id = :vid ORDER BY "order"', vid=video_id)
    )
    return [SceneResponse(**r) for r in rows]


@router.get("/{video_id}/progress", response_model=ProgressResponse)
async def get_progress(video_id: int):
    prog = progress_tracker.get(video_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Nessun progresso attivo")
    return prog


@router.post("/{video_id}/generate-script", response_model=GenerateScriptResponse)
async def generate_script(
    video_id: int, req: GenerateScriptRequest,
    db: DB = Depends(get_db), _user: str = Depends(require_auth),
):
    video_row = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
    if not video_row:
        raise HTTPException(status_code=404, detail="Video non trovato")

    generator = ScriptGenerator()
    script_data = await generator.generate(topic=req.topic, duration_sec=req.duration_seconds, style=req.style, scene_count=req.scene_count)

    if req.target_language:
        translator = TranslatorService()
        for scene in script_data["scenes"]:
            scene["content"] = await translator.translate(scene["content"], req.target_language)
            scene["subtitle_text"] = scene["content"]
        script_data["full_script"] = "\n\n".join(s["content"] for s in script_data["scenes"])

    # Update video with script
    await db.execute(
        sql("UPDATE videos SET script = :script, status = 'script_ready' WHERE id = :id",
            script=script_data["full_script"], id=video_id)
    )

    # Insert scenes
    for i, s in enumerate(script_data["scenes"]):
        await db.execute(
            sql("""INSERT INTO scenes (video_id, "order", content, image_prompt, subtitle_text, duration)
                   VALUES (:vid, :ord, :content, :img, :sub, :dur)""",
                vid=video_id, ord=i, content=s["content"],
                img=s.get("image_prompt", ""),
                sub=s.get("subtitle_text", s["content"]),
                dur=s.get("duration", 5.0))
        )

    return GenerateScriptResponse(video_id=video_id, script=script_data["full_script"], scenes=script_data["scenes"])


@router.post("/{video_id}/render", response_model=VideoResponse)
async def render_video(video_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    video_row = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
    if not video_row:
        raise HTTPException(status_code=404, detail="Video non trovato")

    if video_row["status"] not in ("script_ready", "error", "assets_ready"):
        raise HTTPException(
            status_code=400,
            detail=f"Video in stato '{video_row['status']}', non renderizzabile. Genera prima lo script."
        )

    await db.execute(
        sql("UPDATE videos SET status = 'rendering', progress_step = 'Rendering in corso...' WHERE id = :id", id=video_id)
    )

    try:
        generate_video_task.apply_async(args=[video_id], ignore_result=True)
    except Exception:
        pass

    # Always run inline rendering (synchronous within the HTTP request)
    from app.workers.tasks import _generate_video

    class _Stub:
        def update_state(self, *a, **kw): pass
        request = type("R", (), {})()

    try:
        await _generate_video(video_id, _Stub())
    except Exception as e:
        logger.error(f"Rendering fallito: {e}")

    updated = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
    return VideoResponse(**updated)


@router.post("/{video_id}/compile", response_model=VideoResponse)
async def compile_video(video_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    """Compila il video finale scaricando asset da Supabase Storage (solo step ffmpeg)."""
    from app.workers.tasks import _compile_assets

    video_row = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
    if not video_row:
        raise HTTPException(status_code=404, detail="Video non trovato")

    if video_row["status"] not in ("assets_ready", "error"):
        raise HTTPException(
            status_code=400,
            detail=f"Video in stato '{video_row['status']}', impossibile compilare. Serve lo stato 'assets_ready'."
        )

    await db.execute(
        sql("UPDATE videos SET status = 'compiling', progress_step = 'Compilazione video...' WHERE id = :id",
            id=video_id)
    )

    try:
        await _compile_assets(video_id)
    except Exception as e:
        logger.error(f"Compilazione fallita: {e}")

    updated = await db.fetch_one(sql("SELECT * FROM videos WHERE id = :id", id=video_id))
    return VideoResponse(**updated)


@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    video_row = await db.fetch_one(sql("SELECT id, output_url FROM videos WHERE id = :id", id=video_id))
    if not video_row:
        raise HTTPException(status_code=404, detail="Video non trovato")

    storage = get_supabase_storage()
    if video_row.get("output_url"):
        await storage.delete_file(f"videos/video_{video_id}.mp4")

    await db.execute(sql("DELETE FROM videos WHERE id = :id", id=video_id))
