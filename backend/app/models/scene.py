from __future__ import annotations

import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, default="")
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str] = mapped_column(String(500), default="")
    audio_path: Mapped[str] = mapped_column(String(500), default="")
    subtitle_text: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[float] = mapped_column(Float, default=5.0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    video: Mapped["Video"] = relationship("Video", back_populates="scenes")
