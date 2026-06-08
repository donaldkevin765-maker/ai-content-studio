from __future__ import annotations
from datetime import datetime
from loguru import logger


class ProgressTracker:
    def __init__(self):
        self._store: dict[int, dict] = {}

    def start(self, video_id: int, total_scenes: int):
        self._store[video_id] = {
            "video_id": video_id,
            "status": "starting",
            "total_scenes": total_scenes,
            "current_scene": 0,
            "current_step": "",
            "percent": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            "errors": [],
        }
        logger.info(f"Progress start: video={video_id}, scenes={total_scenes}")

    def update(self, video_id: int, scene: int, step: str):
        if video_id not in self._store:
            return
        total = self._store[video_id]["total_scenes"]
        self._store[video_id].update({
            "status": "processing",
            "current_scene": scene,
            "current_step": step,
            "percent": round((scene / max(total, 1)) * 100, 1),
        })

    def add_error(self, video_id: int, error: str):
        if video_id in self._store:
            self._store[video_id]["errors"].append(error)

    def finish(self, video_id: int):
        if video_id in self._store:
            self._store[video_id].update({
                "status": "completed",
                "percent": 100.0,
                "finished_at": datetime.utcnow().isoformat(),
            })

    def fail(self, video_id: int, error: str):
        if video_id in self._store:
            self._store[video_id].update({
                "status": "failed",
                "error": error,
                "finished_at": datetime.utcnow().isoformat(),
            })

    def get(self, video_id: int) -> dict | None:
        return self._store.get(video_id)

    def remove(self, video_id: int):
        self._store.pop(video_id, None)


progress_tracker = ProgressTracker()
