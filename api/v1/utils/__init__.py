from typing import Any, Optional

import structlog

try:
    from asgi_correlation_id import correlation_id
except ImportError:
    correlation_id = None


def get_logger(name: Optional[str] = None, **bind: Any):
    logger = structlog.get_logger(name) if name else structlog.get_logger()
    if correlation_id is not None:
        request_id = correlation_id.get()
        if request_id is not None:
            logger = logger.bind(request_id=request_id)
    if name:
        logger = logger.bind(component=name.split(".")[-1])
    if bind:
        logger = logger.bind(**bind)
    return logger
