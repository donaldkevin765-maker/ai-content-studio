from __future__ import annotations
import os
import datetime
from pathlib import Path
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings


# --- Decisione runtime: Supabase (cloud) vs SQLite (locale) ---
_use_supabase = os.environ.get("SUPABASE_ACCESS_TOKEN") or settings.supabase_access_token

# --- SQLAlchemy engine per SQLite locale ---
_engine = None
_session_factory = None


def is_supabase():
    return bool(_use_supabase)


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


def _resolve_db_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
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
        kw.update({
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_pre_ping": True,
            "connect_args": {"ssl": "require"},
        })
    return kw


# --- Utility per formattare SQL in modo sicuro ---
def sql(sql_template: str, **params) -> str:
    """Sostituisce :param nella query con valori escapati."""
    for k, v in params.items():
        if v is None:
            replacement = "NULL"
        elif isinstance(v, bool):
            replacement = "TRUE" if v else "FALSE"
        elif isinstance(v, int):
            replacement = str(v)
        elif isinstance(v, float):
            replacement = str(v)
        elif isinstance(v, datetime.datetime):
            replacement = f"'{v.isoformat()}'"
        elif isinstance(v, str):
            replacement = "'" + v.replace("'", "''") + "'"
        else:
            replacement = "'" + str(v).replace("'", "''") + "'"
        sql_template = sql_template.replace(f":{k}", replacement)
    return sql_template


# --- Wrapper universale DB (funziona con SQLite e Supabase) ---
class DB:
    """Wrapper che espone fetch_one / fetch_all / execute su entrambi i backend."""

    def __init__(self, backend):
        self._backend = backend

    async def fetch_one(self, query: str) -> Optional[dict]:
        """SELECT → dict o None."""
        try:
            if isinstance(self._backend, AsyncSession):
                result = await self._backend.execute(text(query))
                row = result.mappings().first()
                if row:
                    return dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
                return None
            return await self._backend.fetch_one(query)
        except Exception as e:
            logger.error(f"fetch_one error: {e} | query: {query[:200]}")
            raise

    async def fetch_all(self, query: str) -> list[dict]:
        """SELECT → list[dict]."""
        try:
            if isinstance(self._backend, AsyncSession):
                result = await self._backend.execute(text(query))
                rows = result.mappings().all()
                return [dict(r._mapping) if hasattr(r, '_mapping') else dict(r) for r in rows]
            return await self._backend.fetch_all(query)
        except Exception as e:
            logger.error(f"fetch_all error: {e} | query: {query[:200]}")
            raise

    async def execute(self, query: str) -> None:
        """INSERT / UPDATE / DELETE."""
        try:
            if isinstance(self._backend, AsyncSession):
                await self._backend.execute(text(query))
            else:
                await self._backend.execute(query)
        except Exception as e:
            logger.error(f"execute error: {e} | query: {query[:200]}")
            raise

    async def commit(self) -> None:
        if isinstance(self._backend, AsyncSession):
            await self._backend.commit()


class DBContext:
    """Context manager per DB wrapper."""

    def __init__(self):
        if is_supabase():
            from app.supabase_db import SupabaseDB
            self._backend = SupabaseDB()
        else:
            self._backend = get_session_factory()()

    async def __aenter__(self) -> DB:
        self._db = DB(self._backend)
        return self._db

    async def __aexit__(self, *args):
        if isinstance(self._backend, AsyncSession):
            await self._backend.close()
        else:
            await self._backend.close()


# --- Dipendenza FastAPI ---
async def get_db():
    async with DBContext() as db:
        yield db


# --- Inizializzazione ---
async def init_db():
    if is_supabase():
        logger.info("Supabase attivo — tabelle già create. Skip init_db().")
        return True

    engine = get_engine()
    try:
        async with engine.begin() as conn:
            from app.models import project, video, scene, user
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database SQLite pronto")
        return True
    except Exception as e:
        if os.environ.get("VERCEL") == "1":
            logger.warning(f"DB init skipped: {e}")
            return False
        raise


class Base(DeclarativeBase):
    pass
