from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, BigInteger
from app.database import Base


class AgentSchedule(Base):
    __tablename__ = "agent_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False)
    project_id = Column(Integer, nullable=False)
    video_id = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    topic = Column(String(255), nullable=False)
    duration_sec = Column(Integer, default=60)
    style = Column(String(64), default="informativo")
    language = Column(String(16), default="it")
    interval_seconds = Column(BigInteger, default=86400)
    next_run = Column(DateTime, nullable=False)
    last_run = Column(DateTime, nullable=True)
    last_video_id = Column(Integer, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
