from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import DB, get_db, sql
from app.models.project import Project
from app.models.video import Video
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, PaginatedProjectResponse
from app.auth import require_auth
from app.services.webhook import WebhookService
from app.supabase_client import get_supabase_storage

router = APIRouter()
webhook = WebhookService()


@router.get("/", response_model=PaginatedProjectResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: DB = Depends(get_db),
    _user: str = Depends(require_auth),
):
    total_row = await db.fetch_one("SELECT COUNT(*) as cnt FROM projects")
    total = total_row["cnt"] if total_row else 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    rows = await db.fetch_all(
        sql("SELECT * FROM projects ORDER BY created_at DESC LIMIT :limit OFFSET :offset",
            limit=page_size, offset=offset)
    )

    return PaginatedProjectResponse(
        items=[ProjectResponse(**r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    row = await db.fetch_one(
        sql("INSERT INTO projects (title, description, language) VALUES (:title, :desc, :lang) RETURNING *",
            title=data.title, desc=data.description, lang=data.language)
    )
    if not row:
        raise HTTPException(status_code=500, detail="Creazione progetto fallita")
    return ProjectResponse(**row)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    row = await db.fetch_one(sql("SELECT * FROM projects WHERE id = :id", id=project_id))
    if not row:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    return ProjectResponse(**row)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    existing = await db.fetch_one(sql("SELECT id FROM projects WHERE id = :id", id=project_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    updates = data.model_dump(exclude_unset=True)
    if updates:
        set_clause = ", ".join(f"{k} = :_{k}" for k in updates)
        params = {f"_{k}": v for k, v in updates.items()}
        params["id"] = project_id
        row = await db.fetch_one(
            sql(f"UPDATE projects SET {set_clause} WHERE id = :id RETURNING *", **params)
        )
    else:
        row = await db.fetch_one(sql("SELECT * FROM projects WHERE id = :id", id=project_id))

    if not row:
        raise HTTPException(status_code=500, detail="Aggiornamento fallito")
    return ProjectResponse(**row)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    existing = await db.fetch_one(sql("SELECT id FROM projects WHERE id = :id", id=project_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    # Clean up storage files
    storage = get_supabase_storage()
    video_rows = await db.fetch_all(sql("SELECT id FROM videos WHERE project_id = :pid", pid=project_id))
    for r in video_rows:
        await storage.delete_file(f"videos/video_{r['id']}.mp4")

    await db.execute(sql("DELETE FROM projects WHERE id = :id", id=project_id))
