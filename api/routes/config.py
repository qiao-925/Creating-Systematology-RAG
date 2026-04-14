"""Configuration endpoints — GET / PUT + model list."""

from __future__ import annotations

from fastapi import APIRouter

from api.deps import get_app_state
from api.schemas import AppConfigResponse, AppConfigUpdate, ModelInfo
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger("api.config")
router = APIRouter(tags=["config"])


@router.get("/config", response_model=AppConfigResponse)
async def get_config():
    rc = get_app_state().runtime_config
    return AppConfigResponse(
        selected_model=rc.selected_model,
        llm_preset=rc.llm_preset,
        retrieval_strategy=rc.retrieval_strategy,
        use_agentic_rag=rc.use_agentic_rag,
        similarity_top_k=rc.similarity_top_k,
        similarity_threshold=rc.similarity_threshold,
        enable_rerank=rc.enable_rerank,
        show_reasoning=rc.show_reasoning,
        research_mode=rc.research_mode,
    )


@router.put("/config", response_model=AppConfigResponse)
async def update_config(body: AppConfigUpdate):
    state = get_app_state()
    rc = state.runtime_config

    changed = False
    for field_name, value in body.model_dump(exclude_unset=True).items():
        if getattr(rc, field_name) != value:
            setattr(rc, field_name, value)
            changed = True

    if changed and state.ready:
        logger.info("Config changed, rebuilding services", changes=body.model_dump(exclude_unset=True))
        state.rebuild_services()

    return await get_config()


@router.get("/config/models", response_model=list[ModelInfo])
async def list_models():
    models = config.get_available_llm_models()
    return [
        ModelInfo(
            id=m.id,
            name=m.name,
            supports_reasoning=m.supports_reasoning,
        )
        for m in models
    ]
