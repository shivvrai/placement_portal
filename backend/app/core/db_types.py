"""
Cross-database type aliases.

When DATABASE_URL uses SQLite, we swap out PostgreSQL-specific types
(ARRAY, JSONB, UUID, Vector) for standard SQLAlchemy equivalents.
This lets the entire backend run on SQLite for local dev without Docker,
and switch back to PostgreSQL (with pgvector) just by changing the env var.
"""

import os
from sqlalchemy import types as sa_types
from app.core.config import get_settings

DATABASE_URL = os.getenv("DATABASE_URL") or get_settings().DATABASE_URL
IS_SQLITE = DATABASE_URL.startswith("sqlite")


# ─── UUID ─────────────────────────────────────────────────────────
# PostgreSQL: native UUID type with as_uuid=True
# SQLite: stored as VARCHAR(36)
if IS_SQLITE:
    class UUIDType(sa_types.TypeDecorator):
        impl = sa_types.String(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return str(value) if value is not None else None

        def process_result_value(self, value, dialect):
            import uuid
            return uuid.UUID(value) if value is not None else None
else:
    from sqlalchemy.dialects.postgresql import UUID as _PG_UUID

    class UUIDType(sa_types.TypeDecorator):
        impl = _PG_UUID(as_uuid=True)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return value

        def process_result_value(self, value, dialect):
            return value


# ─── ARRAY ────────────────────────────────────────────────────────
# PostgreSQL: native ARRAY
# SQLite: stored as JSON string
if IS_SQLITE:
    import json

    class ArrayType(sa_types.TypeDecorator):
        impl = sa_types.Text
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return json.dumps(value) if value is not None else None

        def process_result_value(self, value, dialect):
            return json.loads(value) if value is not None else None

    def ARRAY(item_type):
        return ArrayType()

else:
    from sqlalchemy.dialects.postgresql import ARRAY  # noqa: F811


# ─── JSON / JSONB ─────────────────────────────────────────────────
# PostgreSQL: JSONB (binary JSON with indexing)
# SQLite: standard JSON
if IS_SQLITE:
    JSONB = sa_types.JSON
else:
    from sqlalchemy.dialects.postgresql import JSONB  # noqa: F811


# ─── Vector (pgvector) ────────────────────────────────────────────
# PostgreSQL: pgvector Vector(384)
# SQLite: stored as JSON array (no ANN search — just storage)
if IS_SQLITE:
    import json

    class VectorType(sa_types.TypeDecorator):
        impl = sa_types.Text
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return json.dumps(value) if value is not None else None

        def process_result_value(self, value, dialect):
            return json.loads(value) if value is not None else None

    def Vector(dim):
        return VectorType()

else:
    from pgvector.sqlalchemy import Vector  # noqa: F811
