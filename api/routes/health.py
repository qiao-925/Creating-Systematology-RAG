"""Health check endpoint."""

from fastapi import APIRouter

from api.deps import get_app_state
from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    state = get_app_state()

    if state.error:
        return HealthResponse(status="error", message=state.error)

    if not state.ready:
        return HealthResponse(status="initializing", message="Service is starting up")

    return HealthResponse(status="ready", message="OK")
