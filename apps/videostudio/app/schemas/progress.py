from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class ProgressResponse(BaseModel):
    video_id: int
    status: str
    total_scenes: int
    current_scene: int
    current_step: str
    percent: float
    started_at: str
    errors: list[str]
    finished_at: Optional[str] = None
    error: Optional[str] = None
