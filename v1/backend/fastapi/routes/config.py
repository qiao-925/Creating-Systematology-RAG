"""Configuration endpoints — GET + model list."""

from __future__ import annotations

from fastapi import APIRouter

from backend.fastapi.schemas import AppConfigResponse, ModelInfo
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger("api.config")
router = APIRouter(tags=["config"])


@router.get("/config", response_model=AppConfigResponse)
async def get_config():
    return AppConfigResponse(
        selected_model=config.get_default_llm_id(),
        llm_preset="balanced",
        retrieval_strategy=config.RETRIEVAL_STRATEGY,
        similarity_top_k=config.SIMILARITY_TOP_K,
        similarity_threshold=config.SIMILARITY_THRESHOLD,
        enable_rerank=config.ENABLE_RERANK,
        show_reasoning=config.DEEPSEEK_ENABLE_REASONING_DISPLAY,
    )


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
