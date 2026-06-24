from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.api.dependencies import get_transcription_service
from app.api.schemas.transcription import (
    TranscriptionJobListItem,
    TranscriptionJobListResponse,
    TranscriptionJobResponse,
)
from app.application.services.transcription_service import (
    TranscriptionService,
)
from app.domain.enums import TranscriptionJobStatus

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


@router.get('/{job_id}', response_model=TranscriptionJobResponse)
async def get_transcription_job(
    job_id: UUID,
    service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionJobResponse:
    job = service.get_transcription_job(str(job_id))
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Transcription job not found.',
        )
    return TranscriptionJobResponse.model_validate(job)


@router.get('', response_model=TranscriptionJobListResponse)
async def list_transcription_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: TranscriptionJobStatus | None = Query(
        default=None, alias='status'
    ),
    service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionJobListResponse:
    status_value = status_filter.value if status_filter is not None else None
    items, total = service.list_transcription_jobs(
        status=status_value, limit=limit, offset=offset
    )
    return TranscriptionJobListResponse(
        items=[TranscriptionJobListItem.model_validate(job) for job in items],
        limit=limit,
        offset=offset,
        total=total,
    )
