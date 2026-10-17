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
    page_size: Optional[int] = None
    total_items: Optional[int] = None

    def model_post_init(self, __context: Any) -> None:
        if self.page_size is None:
            self.page_size = self.per_page
        if self.total_items is None:
            self.total_items = self.total


class PaginatedResponse(BaseModel):
    data: list[Any]
    meta: Optional[PaginationMeta] = None
    pagination: Optional[PaginationMeta] = None

    def model_post_init(self, __context: Any) -> None:
        if self.meta is not None and self.pagination is None:
            self.pagination = self.meta
        elif self.pagination is not None and self.meta is None:
            self.meta = self.pagination


class IDResponse(BaseModel):
    id: uuid.UUID


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
