from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
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
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(require_auth),
):
    total_q = await db.execute(select(sql_func.count(Project.id)))
    total = total_q.scalar() or 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Project).offset(offset).limit(page_size).order_by(Project.created_at.desc())
    )
    items = result.scalars().all()

    return PaginatedProjectResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    project = Project(title=data.title, description=data.description, language=data.language)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db), _user: str = Depends(require_auth)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    storage = get_supabase_storage()
    videos_q = await db.execute(select(Video.id).where(Video.project_id == project_id))
    for (vid,) in videos_q:
        await storage.delete_file(f"videos/video_{vid}.mp4")

    await db.delete(project)
    await db.commit()
