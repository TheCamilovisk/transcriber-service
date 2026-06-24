from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_transcription_service
from app.api.schemas.transcription import TranscriptionJobResponse
from app.application.services.transcription_service import (
    TranscriptionService,
)

router = APIRouter(prefix='/api/v1/transcriptions', tags=['transcriptions'])


@router.post('', response_model=TranscriptionJobResponse, status_code=201)
async def create_transcription_job(
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionJobResponse:
    content = await audio.read()
    job = service.create_transcription_job(
        original_filename=audio.filename or 'unknown',
        content=content,
        content_type=audio.content_type,
        language=language,
    )
    return TranscriptionJobResponse.model_validate(job)
