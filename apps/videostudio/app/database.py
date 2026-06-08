from __future__ import annotations
import os
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


def _resolve_db_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "sslmode" not in url and "ssl=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        logger.info(f"Usando Postgres: {url.split('@')[-1].split('?')[0]}")
        return url
    if os.environ.get("VERCEL") == "1":
        db_path = Path("/tmp/data/video_ai.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.warning(f"Nessuna DATABASE_URL, uso SQLite effimero su {db_path} (dati persi a ogni cold start)")
        return f"sqlite+aiosqlite:///{db_path}"
    return settings.database_url


def _build_engine_kwargs(url: str) -> dict:
    kw: dict = {"echo": False}
    if "postgresql" in url:
        kw.update({"pool_size": settings.database_pool_size, "max_overflow": settings.database_max_overflow, "pool_pre_ping": True})
    return kw


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        url = _resolve_db_url()
        _engine = create_async_engine(url, **_build_engine_kwargs(url))
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def get_db():
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session() -> AsyncSession:
    return get_session_factory()()


async def init_db():
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            from app.models import project, video, scene
            await conn.run_sync(Base.metadata.create_all)
        return True
    except Exception as e:
        if os.environ.get("VERCEL") == "1":
            from loguru import logger
            logger.warning(f"DB init skipped (no DATABASE_URL): {e}")
            return False
        raise


class Base(DeclarativeBase):
    pass
