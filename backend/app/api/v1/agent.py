from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth import require_auth
from app.database import DB, get_db, sql
from app.services.agent import VideoAgent, AgentScheduler

router = APIRouter()
agent = VideoAgent()


@router.post("/chat")
async def agent_chat(prompt: str, _user: str = Depends(require_auth)):
    """
    Invia un prompt all'agente AI.
    L'agente analizza la richiesta, crea progetto + video, genera script e avvia il render.
    Restituisce subito un task_id per fare polling sullo stato.
    """
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail="Il prompt non può essere vuoto")

    task = await agent.plan(prompt.strip())
    return {
        "task_id": task.task_id,
        "project_id": task.project_id,
        "video_id": task.video_id,
        "topic": task.topic,
        "status": task.status,
        "schedule": task.schedule,
        "message": "Video in elaborazione. Usa GET /agent/tasks/{task_id} per lo stato.",
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, _user: str = Depends(require_auth)):
    """Polling dello stato di un task agente."""
    task = VideoAgent.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task non trovato")
    return task.to_dict()


@router.get("/tasks")
async def list_tasks(limit: int = Query(20, ge=1, le=100), _user: str = Depends(require_auth)):
    """Lista degli ultimi task eseguiti."""
    tasks = VideoAgent.list_tasks(limit)
    return [t.to_dict() for t in tasks]


@router.post("/schedule/check")
async def check_schedules(_user: str = Depends(require_auth)):
    """
    Controlla ed esegue le schedule scadute.
    Utile per test manuali o da GitHub Actions cron.
    """
    await AgentScheduler.check_and_run()
    return {"status": "ok", "message": "Schedule controllate"}


@router.get("/schedules")
async def list_schedules(db: DB = Depends(get_db), _user: str = Depends(require_auth)):
    """Lista delle schedule attive."""
    try:
        rows = await db.fetch_all(
            sql("SELECT * FROM agent_schedules ORDER BY next_run ASC")
        )
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tabella non disponibile: {e}")
