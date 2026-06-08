from __future__ import annotations

import datetime
from pydantic import BaseModel
from typing import Optional


class SceneResponse(BaseModel):
    id: int
    video_id: int
    order: int
    content: str
    image_prompt: str
    image_path: str
    audio_path: str
    subtitle_text: str
    duration: float

    model_config = {"from_attributes": True}
