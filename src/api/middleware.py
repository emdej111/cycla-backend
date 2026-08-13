import logging
import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("cycla")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Tags every request with an id and logs method/path/status/duration.
    Never logs request bodies, since check-ins and chat messages carry
    sensitive health data.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %s (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


def register_middleware(app: FastAPI) -> None:
    from fastapi.middleware.cors import CORSMiddleware

    from src.core.config import get_settings

    settings = get_settings()
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
