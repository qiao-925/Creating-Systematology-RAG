"""Health check endpoint."""

from fastapi import APIRouter

from backend.fastapi.deps import get_app_state
from backend.fastapi.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    state = get_app_state()

    if state.error:
        return HealthResponse(status="error", message=state.error)

    if not state.ready:
        return HealthResponse(status="initializing", message="Service is starting up")

    return HealthResponse(status="ready", message="OK")
