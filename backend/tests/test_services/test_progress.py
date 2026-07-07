from __future__ import annotations

import pytest
from app.services.progress import ProgressTracker


class TestProgressTracker:
    def setup_method(self):
        self.tracker = ProgressTracker()

    def test_start(self):
        self.tracker.start(1, 5)
        prog = self.tracker.get(1)
        assert prog is not None
        assert prog["total_scenes"] == 5
        assert prog["status"] == "starting"

    def test_update(self):
        self.tracker.start(3, 4)
        self.tracker.update(3, 2, "Generazione audio")
        prog = self.tracker.get(3)
        assert prog["current_scene"] == 2
        assert prog["percent"] == 50.0

    def test_finish(self):
        self.tracker.start(5, 3)
        self.tracker.finish(5)
        prog = self.tracker.get(5)
        assert prog["status"] == "completed"
        assert prog["percent"] == 100.0

    def test_fail(self):
        self.tracker.start(7, 3)
        self.tracker.fail(7, "Errore test")
        prog = self.tracker.get(7)
        assert prog["status"] == "failed"
        assert prog["error"] == "Errore test"

    def test_remove(self):
        self.tracker.start(9, 2)
        self.tracker.remove(9)
        assert self.tracker.get(9) is None

    def test_add_error(self):
        self.tracker.start(11, 3)
        self.tracker.add_error(11, "warn")
        prog = self.tracker.get(11)
        assert "warn" in prog["errors"]
