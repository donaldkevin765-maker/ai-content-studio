"""
AI Agent — Orchestratore conversazionale per la creazione video.

Prende un prompt naturale come "fammi un video di 60 secondi sull'IA"
e orchestra l'intera pipeline: pianificazione → progetto → script → render.
"""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from app.database import DBContext, sql
from app.services.script_generator import ScriptGenerator
from app.services.llm_providers import LLMEnsemble


# ──────────────────────────────────────────────────────────
# Task registry in memoria
# ──────────────────────────────────────────────────────────

class AgentTask:
    def __init__(
        self,
        task_id: str,
        project_id: int,
        video_id: int,
        prompt: str,
        topic: str,
        duration_sec: int,
        style: str,
        language: str,
        schedule: Optional[dict] = None,
    ):
        self.task_id = task_id
        self.project_id = project_id
        self.video_id = video_id
        self.prompt = prompt
        self.topic = topic
        self.duration_sec = duration_sec
        self.style = style
        self.language = language
        self.schedule = schedule
        self.status = "pending"
        self.progress_percent = 0
        self.progress_step = "In coda"
        self.output_url: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "video_id": self.video_id,
            "prompt": self.prompt,
            "topic": self.topic,
            "duration_sec": self.duration_sec,
            "style": self.style,
            "language": self.language,
            "schedule": self.schedule,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "progress_step": self.progress_step,
            "output_url": self.output_url,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


_tasks: dict[str, AgentTask] = {}


# ──────────────────────────────────────────────────────────
# Agent Service
# ──────────────────────────────────────────────────────────

class VideoAgent:
    def __init__(self):
        self.llm = LLMEnsemble()
        self.script_gen = ScriptGenerator()

    # ── Parsing intento ──────────────────────────────────

    async def parse_intent(self, prompt: str) -> dict:
        system = (
            "Sei un assistente che analizza richieste di creazione video. "
            "Estrai i parametri dal testo dell'utente e restituisci SOLO JSON valido."
        )
        user = (
            f'Analizza questa richiesta: "{prompt}"\n\n'
            "Restituisci JSON con:\n"
            '  - "topic": tema principale (stringa, obbligatorio)\n'
            '  - "duration_sec": durata in secondi (numero, default 60)\n'
            '  - "style": informativo | divertente | didattico | motivazionale | serio\n'
            '  - "language": lingua (default "it")\n'
            '  - "schedule": oggetto opzionale (null se non richiesto).\n'
            "    Se l'utente dice 'ogni giorno/settimana/X ore/giorni':\n"
            '      { "tipo": "daily"|"weekly"|"custom", "interval_seconds": N, "start_date": "ISO" }\n\n'
            "Rispondi SOLO con JSON."
        )

        try:
            result = await self.llm.generate(system + "\n\n" + user, max_tokens=1024)
            if result:
                return self._parse_json(result, prompt)
        except Exception as e:
            logger.warning(f"Agent LLM fallito: {e}")

        return self._fallback_intent(prompt)

    def _parse_json(self, text: str, fallback: str) -> dict:
        try:
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            data = json.loads(m.group()) if m else {}
        return {
            "topic": data.get("topic", fallback),
            "duration_sec": int(data.get("duration_sec", 60)),
            "style": data.get("style", "informativo"),
            "language": data.get("language", "it"),
            "schedule": data.get("schedule"),
        }

    def _fallback_intent(self, prompt: str) -> dict:
        durata = re.search(r"(\d+)\s*(secondi|minuti|min|sec|s)", prompt.lower())
        duration_sec = 60
        if durata:
            v = int(durata.group(1))
            duration_sec = v * 60 if durata.group(2) in ("minuti", "min") else v
        stili = ["informativo", "divertente", "didattico", "motivazionale", "serio"]
        style = next((s for s in stili if s in prompt.lower()), "informativo")
        schedule = None
        routine = re.search(
            r"(ogni\s+(\d+)\s*(giorni?|ore?|settimane?)|daily|ogni\s+giorno|quotidianamente|weekly|ogni\s+settimana)",
            prompt.lower(),
        )
        if routine:
            interval = 86400
            if "settiman" in prompt.lower():
                interval = 604800
            if routine.group(2):
                n = int(routine.group(2))
                u = (routine.group(3) or "")[:4]
                interval = n * (3600 if "or" in u else 86400 if "iorn" in u else 604800)
            schedule = {"tipo": "custom", "interval_seconds": interval, "start_date": datetime.utcnow().isoformat()}
        return {"topic": prompt.strip().strip("."), "duration_sec": duration_sec, "style": style, "language": "it", "schedule": schedule}

    # ── Esecuzione ──────────────────────────────────────

    async def plan(self, prompt: str) -> AgentTask:
        """
        Fase 1 (sincrona): analizza prompt, crea progetto + video, genera script,
        avvia render in background. Restituisce subito con task_id per polling.
        """
        intent = await self.parse_intent(prompt)
        task_id = f"agent_{uuid.uuid4().hex[:12]}"
        logger.info(f"Agent plan: {intent['topic']} ({intent['duration_sec']}s, {intent['style']})")

        task = AgentTask(
            task_id=task_id, project_id=0, video_id=0, prompt=prompt,
            topic=intent["topic"], duration_sec=intent["duration_sec"],
            style=intent["style"], language=intent["language"],
            schedule=intent.get("schedule"),
        )
        _tasks[task_id] = task

        try:
            # 1. Crea progetto
            task.progress_step = "Creazione progetto..."
            async with DBContext() as db:
                row = await db.fetch_one(sql(
                    "INSERT INTO projects (title, description, language) VALUES (:t, :d, :l) RETURNING *",
                    t=f"AI: {intent['topic'][:80]}", d=f"Creato dall'assistente AI: {prompt[:200]}", l=intent["language"],
                ))
                task.project_id = row["id"]
                v = await db.fetch_one(sql(
                    "INSERT INTO videos (project_id, title, status) VALUES (:p, :t, 'script_ready') RETURNING *",
                    p=task.project_id, t=intent["topic"][:120],
                ))
                task.video_id = v["id"]

            # 2. Genera script
            task.progress_step = "Generazione script..."
            task.progress_percent = 20
            script = await self.script_gen.generate(
                topic=intent["topic"], duration_sec=intent["duration_sec"],
                style=intent["style"], scene_count=0,
            )
            async with DBContext() as db:
                await db.execute(sql("UPDATE videos SET script = :s WHERE id = :id", s=script["full_script"], id=task.video_id))
                for i, s in enumerate(script["scenes"]):
                    await db.execute(sql(
                        'INSERT INTO scenes (video_id, "order", content, image_prompt, subtitle_text, duration) '
                        "VALUES (:v, :o, :c, :i, :st, :d)",
                        v=task.video_id, o=i, c=s["content"], i=s.get("image_prompt", intent["topic"]),
                        st=s.get("subtitle_text", s["content"]), d=s.get("duration", 5.0),
                    ))

            # 3. Avvia render in background (non bloccante per l'API)
            task.status = "rendering"
            task.progress_percent = 40
            task.progress_step = "Rendering avviato, monitoraggio in corso..."
            asyncio.create_task(self._render_worker(task))

            # 4. Salva schedule se richiesto
            if task.schedule:
                await self._save_schedule(task)

            return task

        except Exception as e:
            logger.error(f"Agent plan error: {e}")
            task.status = "error"
            task.error = str(e)
            task.progress_step = f"Errore: {e}"
            return task

    async def _render_worker(self, task: AgentTask):
        """Worker background: avvia render e aggiorna stato tramite polling DB."""
        try:
            await self._trigger_render(task.video_id)
        except Exception as e:
            task.status = "error"
            task.error = f"Render fallito: {e}"
            task.progress_step = f"Errore: {e}"
            return

        for _ in range(60):
            try:
                async with DBContext() as db:
                    video = await db.fetch_one(sql(
                        "SELECT status, output_url, error_message, progress_percent, progress_step "
                        "FROM videos WHERE id = :id", id=task.video_id
                    ))
                    if not video:
                        break
                    task.progress_percent = video.get("progress_percent") or task.progress_percent
                    task.progress_step = video.get("progress_step") or task.progress_step
                    if video["status"] == "completed":
                        task.status = "completed"
                        task.progress_percent = 100
                        task.progress_step = "Completato!"
                        task.output_url = video.get("output_url")
                        return
                    if video["status"] == "error":
                        task.status = "error"
                        task.error = video.get("error_message", "Errore sconosciuto")
                        task.progress_step = f"Errore: {task.error}"
                        return
                    if video["status"] == "assets_ready":
                        task.progress_step = "Compilazione video finale..."
                        try:
                            await self._trigger_compile(task.video_id)
                        except Exception as e:
                            task.status = "error"
                            task.error = f"Compilazione fallita: {e}"
                            return
            except Exception as e:
                logger.warning(f"Agent poll error: {e}")
            await asyncio.sleep(5)

        if task.status not in ("completed", "error"):
            task.status = "error"
            task.error = "Timeout"
            task.progress_step = "Timeout"

    async def _trigger_render(self, video_id: int):
        from app.workers.tasks import generate_video_task, _generate_video
        try:
            generate_video_task.apply_async(args=[video_id], ignore_result=True)
        except Exception:
            pass

        class _Stub:
            def update_state(self, *a, **kw): pass
            request = type("R", (), {})()

        await _generate_video(video_id, _Stub())

    async def _trigger_compile(self, video_id: int):
        from app.workers.tasks import _compile_assets
        await _compile_assets(video_id)

    async def _save_schedule(self, task: AgentTask):
        try:
            async with DBContext() as db:
                await db.execute(sql(
                    "INSERT INTO agent_schedules (task_id, project_id, video_id, prompt, topic, "
                    "duration_sec, style, language, interval_seconds, next_run, created_at) "
                    "VALUES (:tid, :pid, :vid, :prompt, :topic, :dur, :style, :lang, :int, :next, :now)",
                    tid=task.task_id, pid=task.project_id, vid=task.video_id,
                    prompt=task.prompt, topic=task.topic, dur=task.duration_sec,
                    style=task.style, lang=task.language,
                    int=task.schedule.get("interval_seconds", 86400),
                    next=datetime.utcnow() + timedelta(seconds=task.schedule.get("interval_seconds", 86400)),
                    now=datetime.utcnow(),
                ))
        except Exception as e:
            logger.warning(f"Salvataggio schedule fallito: {e}")

    @staticmethod
    def get_task(task_id: str) -> Optional[AgentTask]:
        return _tasks.get(task_id)

    @staticmethod
    def list_tasks(limit: int = 20) -> list[AgentTask]:
        return sorted(_tasks.values(), key=lambda t: t.created_at, reverse=True)[:limit]


# ──────────────────────────────────────────────────────────
# Scheduler periodico
# ──────────────────────────────────────────────────────────

class AgentScheduler:
    @staticmethod
    async def check_and_run():
        try:
            async with DBContext() as db:
                rows = await db.fetch_all(sql(
                    "SELECT * FROM agent_schedules WHERE next_run <= :now AND active = 1",
                    now=datetime.utcnow(),
                ))
        except Exception:
            return

        agent = VideoAgent()
        for row in rows:
            logger.info(f"Scheduler: esecuzione {row['task_id']}")
            try:
                task = await agent.plan(row["prompt"])
                async with DBContext() as db:
                    await db.execute(sql(
                        "UPDATE agent_schedules SET next_run = :next, last_run = :now, last_video_id = :vid WHERE task_id = :tid",
                        next=datetime.utcnow() + timedelta(seconds=row["interval_seconds"]),
                        now=datetime.utcnow(), vid=task.video_id, tid=row["task_id"],
                    ))
            except Exception as e:
                logger.error(f"Scheduler esecuzione fallita: {e}")
