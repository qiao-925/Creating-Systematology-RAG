"""Chat endpoint — SSE streaming."""

from __future__ import annotations

import json
import traceback
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from api.deps import get_app_state
from api.schemas import ChatRequest
from backend.infrastructure.logger import get_logger

logger = get_logger("api.chat")
router = APIRouter(tags=["chat"])


async def _chat_event_generator(
    message: str,
    session_id: str | None,
) -> AsyncIterator[dict]:
    """Wrap RAGService.stream_chat into SSE events.

    Event types sent to the client:
      - ``token``   : partial text content
      - ``sources`` : list of citation sources (sent once)
      - ``reasoning``: reasoning chain text (sent once, may be absent)
      - ``done``    : signals stream completion
      - ``error``   : error message
    """
    state = get_app_state()
    rag_service = state.rag_service
    if rag_service is None:
        yield {"event": "error", "data": json.dumps({"message": "Service not ready"})}
        return

    try:
        async for chunk in rag_service.stream_chat(message, session_id=session_id):
            if not isinstance(chunk, dict):
                continue

            chunk_type = chunk.get("type", "")
            chunk_data = chunk.get("data")

            if chunk_type == "token":
                # Token text — the main streaming content
                text = chunk_data if isinstance(chunk_data, str) else ""
                if text:
                    yield {"event": "token", "data": json.dumps({"content": text})}

            elif chunk_type == "sources":
                # Citation sources list
                raw_sources = chunk_data if isinstance(chunk_data, list) else []
                sources_data = []
                for s in raw_sources:
                    if hasattr(s, "model_dump"):
                        sources_data.append(s.model_dump())
                    elif isinstance(s, dict):
                        sources_data.append(s)
                if sources_data:
                    yield {"event": "sources", "data": json.dumps(sources_data)}

            elif chunk_type == "reasoning":
                # Reasoning chain content
                reasoning_text = chunk_data if isinstance(chunk_data, str) else ""
                if reasoning_text:
                    yield {"event": "reasoning", "data": json.dumps({"content": reasoning_text})}

            elif chunk_type == "done":
                # Stream complete — forward session info
                done_data = chunk_data if isinstance(chunk_data, dict) else {}
                yield {"event": "done", "data": json.dumps({"status": "complete", **done_data})}
                return

            elif chunk_type == "error":
                err_msg = (chunk_data or {}).get("message", "Unknown error") if isinstance(chunk_data, dict) else str(chunk_data)
                yield {"event": "error", "data": json.dumps({"message": err_msg})}
                return

        # Fallback done if stream ended without explicit done event
        yield {"event": "done", "data": json.dumps({"status": "complete"})}

    except Exception as e:
        logger.error("Chat stream error", error=str(e), exc_info=True)
        yield {
            "event": "error",
            "data": json.dumps({"message": str(e), "traceback": traceback.format_exc()}),
        }


@router.post("/chat")
async def chat(req: ChatRequest):
    state = get_app_state()
    if not state.ready or state.rag_service is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    return EventSourceResponse(
        _chat_event_generator(req.message, req.session_id),
        media_type="text/event-stream",
    )
