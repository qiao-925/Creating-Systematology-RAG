"""Dependency injection for FastAPI routes.

Manages application state and lifecycle.
Initialised once during FastAPI lifespan; routes obtain singletons via
``get_app_state()``.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger("api.deps")


@dataclass
class AppState:
    """Application-wide singleton state, populated during lifespan startup."""

    init_result: Optional[Any] = None
    ready: bool = False
    error: Optional[str] = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set_ready(self) -> None:
        with self._lock:
            self.ready = True


# ── module-level singleton ───────────────────────────

_app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state
