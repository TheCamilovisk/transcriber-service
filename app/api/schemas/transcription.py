from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _TranscriptionJobBase(BaseModel):
    """Shared fields between full response and list item."""

    id: str
    status: str
    original_filename: str
    content_type: str | None
    file_size_bytes: int
    language: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class TranscriptionJobResponse(_TranscriptionJobBase):
    """Full job representation. Includes text."""

    text: str | None

    model_config = ConfigDict(from_attributes=True)


class TranscriptionJobListItem(_TranscriptionJobBase):
    """Summary representation. Does not include text."""

    model_config = ConfigDict(from_attributes=True)


class TranscriptionJobListResponse(BaseModel):
    items: list[TranscriptionJobListItem]
    limit: int
    offset: int
    total: int
