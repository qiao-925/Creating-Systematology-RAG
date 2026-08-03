"""
Observability bootstrap: register instrumentation handlers with LlamaIndex.

Call `enable_instrumentation()` once at startup to activate event + span
tracing via the modern Instrumentation API.
"""

from backend.infrastructure.logger import get_logger

logger = get_logger("observability_setup")

_initialized = False


def enable_instrumentation() -> bool:
    """Register event and span handlers with the LlamaIndex root dispatcher.

    Safe to call multiple times — handlers are registered only once.

    Returns:
        True if handlers were registered, False if already initialized.
    """
    global _initialized
    if _initialized:
        return False

    try:
        from llama_index.core.instrumentation import get_dispatcher
        from backend.infrastructure.observers.instrumentation import (
            ObservabilityEventHandler,
            ObservabilitySpanHandler,
        )

        dispatcher = get_dispatcher()
        dispatcher.add_event_handler(ObservabilityEventHandler())
        dispatcher.add_span_handler(ObservabilitySpanHandler())

        _initialized = True
        logger.info("instrumentation_enabled", handlers=["event", "span"])
        return True

    except Exception as e:
        logger.warning("instrumentation_setup_failed", error=str(e))
        return False
