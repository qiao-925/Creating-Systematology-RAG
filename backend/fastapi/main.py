"""FastAPI application entry point.

Startup lifecycle:
  1. lifespan() calls ``initialize_app()`` (same logic as the old Streamlit preloader)
  2. On success, ``AppState.ready`` is set to True and services are built
  3. Routes become available

Run:
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path so ``backend.*`` imports work.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.infrastructure.logger import get_logger

logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    from backend.fastapi.deps import get_app_state

    state = get_app_state()

    # ── startup ──────────────────────────────────────
    logger.info("🚀 FastAPI lifespan: starting initialization")
    try:
        from backend.infrastructure.initialization.bootstrap import initialize_app

        init_result = initialize_app()
        state.init_result = init_result

        if not init_result.all_required_ready:
            state.error = f"Required modules failed: {', '.join(init_result.failed_modules)}"
            logger.error(state.error)
        else:
            state.set_ready()
            logger.info("✅ FastAPI ready")
    except Exception as exc:
        state.error = str(exc)
        logger.error("❌ Initialization failed", error=str(exc), exc_info=True)

    yield  # ← app is running

    # ── shutdown ─────────────────────────────────────
    logger.info("🛑 FastAPI lifespan: shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Systematology API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow origins from env or default to wildcard
    import os
    cors_env = os.getenv("CORS_ORIGINS", "")
    if cors_env:
        allow_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    else:
        allow_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register route modules
    from backend.fastapi.routes.health import router as health_router
    from backend.fastapi.routes.config import router as config_router
    from backend.core.api import router as systematology_router

    app.include_router(health_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    app.include_router(systematology_router)

    return app


app = create_app()
