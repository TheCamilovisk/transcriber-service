from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.infrastructure.storage.local_audio_storage import LocalAudioStorage
from app.settings import get_settings

router = APIRouter(tags=['health'])


@router.get('/health')
def health_check(
    db_session: Session = Depends(get_db_session),
) -> JSONResponse:
    db_status = 'ok'
    upload_status = 'ok'

    try:
        db_session.execute(text('SELECT 1'))
    except Exception:
        db_status = 'error'

    try:
        settings = get_settings()
        storage = LocalAudioStorage(upload_dir=settings.upload_dir)
        storage.validate_writable()
    except Exception:
        upload_status = 'error'

    overall = 'ok' if db_status == 'ok' and upload_status == 'ok' else 'error'
    status_code = 200 if overall == 'ok' else 503

    return JSONResponse(
        content={
            'status': overall,
            'database': db_status,
            'upload_dir': upload_status,
        },
        status_code=status_code,
    )
