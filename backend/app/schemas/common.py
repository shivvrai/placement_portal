"""Pydantic schemas — common base types shared across domains."""

import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    data: list[Any]
    meta: PaginationMeta


class IDResponse(BaseModel):
    id: uuid.UUID


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
