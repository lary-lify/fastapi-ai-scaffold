import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Inject ``X-Request-ID`` and log method / path / status / latency."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        cost_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "method=%s path=%s status=%s cost_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            cost_ms,
            request_id,
        )
        return response
