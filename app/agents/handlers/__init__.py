from app.agents.handlers.base import (
    SegmentHandler, HandlerResult, HANDLER_REGISTRY, register_handler,
)

# Import handler modules to trigger registration via register_handler() calls
from . import diagnostic  # noqa: F401

__all__ = ["SegmentHandler", "HandlerResult", "HANDLER_REGISTRY", "register_handler"]
