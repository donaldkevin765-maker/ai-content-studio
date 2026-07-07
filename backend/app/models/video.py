from __future__ import annotations

import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    script: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    progress_step: Mapped[str] = mapped_column(String(255), default="")
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    output_path: Mapped[str] = mapped_column(String(500), default="")
    output_url: Mapped[str] = mapped_column(String(1000), default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship("Project", back_populates="videos")
    scenes: Mapped[list["Scene"]] = relationship("Scene", back_populates="video", cascade="all, delete-orphan")
