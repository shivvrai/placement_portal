import time
import uuid
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging_config import logger

def _generate_uuid8() -> str:
    """Generate a pseudo-UUIDv8 string."""
    t_ns = time.time_ns()
    rand_bytes = os.urandom(8)
    time_bytes = t_ns.to_bytes(8, byteorder="big")
    uuid_bytes = bytearray(time_bytes + rand_bytes)
    # version 8 nybble
    uuid_bytes[6] = (uuid_bytes[6] & 0x0f) | 0x80
    # variant 10 (RFC 4122)
    uuid_bytes[8] = (uuid_bytes[8] & 0x3f) | 0x80
    return str(uuid.UUID(bytes=bytes(uuid_bytes)))

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = _generate_uuid8()
        # Store for logging
        import structlog
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            request_method=request.method,
            request_path=request.url.path,
        )
        
        start_time = time.perf_counter()
        response = await call_next(request)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
        
        logger.info(
            "Request handled",
            latency_ms=round(latency_ms, 2),
            status_code=response.status_code
        )
        
        structlog.contextvars.clear_contextvars()
        return response
