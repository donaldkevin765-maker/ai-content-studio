from __future__ import annotations

import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.scene import SceneResponse


class VideoCreate(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=255)


class VideoResponse(BaseModel):
    id: int
    project_id: int
    title: str
    script: str
    status: str
    progress_percent: float
    progress_step: str
    duration: float
    output_path: str
    output_url: str
    error_message: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class VideoDetailResponse(VideoResponse):
    scenes: list[SceneResponse] = []


class GenerateScriptRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    duration_seconds: int = Field(default=60, ge=10, le=600)
    style: str = Field(default="informativo", pattern=r"^(informativo|divertente|serio|motivazionale|didattico)$")
    target_language: Optional[str] = None


class GenerateScriptResponse(BaseModel):
    video_id: int
    script: str
    scenes: list[dict]


class PaginatedVideoResponse(BaseModel):
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
