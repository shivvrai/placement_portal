import re
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.security import decode_token
from app.core.logging_config import logger

# Paths where we enforce UUID matching for students
STUDENT_BLOCKED_PATH_PATTERNS = [
    r"^/api/v1/students/(?P<uuid_segment>[0-9a-fA-F\-]{36})/?$",
    r"^/api/v1/applications/(?P<uuid_segment>[0-9a-fA-F\-]{36})/?$"
]

COMPILED_PATTERNS = [re.compile(p) for p in STUDENT_BLOCKED_PATH_PATTERNS]

class RowLevelSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
            
        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            role = payload.get("role")
            user_id = payload.get("sub")
            
            if role == "student" and user_id:
                path = request.url.path
                for pattern in COMPILED_PATTERNS:
                    match = pattern.match(path)
                    if match:
                        path_uuid = match.group("uuid_segment")
                        if path_uuid != user_id:
                            logger.warning(
                                "UNAUTHORIZED_ACCESS_ATTEMPT",
                                actor_id=user_id,
                                attempted_path=path,
                                path_uuid=path_uuid
                            )
                            # Safe asynchronous DB audit record without breaking 403 on failure
                            from app.core.database import async_sessionmaker_db
                            from app.core.audit import record_audit_event
                            try:
                                async with async_sessionmaker_db() as db:
                                    await record_audit_event(
                                        db=db,
                                        actor_id=uuid.UUID(user_id),
                                        event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
                                        resource_type="Route",
                                        resource_id=path_uuid,
                                        details={"path": path},
                                        ip_address=request.client.host
                                    )
                                    await db.commit()
                            except Exception:
                                pass # audit failure must NEVER turn the intended 403 into a 500

                            return JSONResponse(
                                status_code=403,
                                content={"detail": "Forbidden: You cannot access resources belonging to other users."}
                            )
        except Exception:
            # Bad token, let normal auth dependencies handle it
            pass
            
        return await call_next(request)
