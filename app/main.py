import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.health import router as health_router
from app.api.routes.transcriptions import router as transcriptions_router
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.storage.local_audio_storage import LocalAudioStorage

logger = logging.getLogger(__name__)


def validate_startup_resources() -> None:
    """Validate required resources on startup. Fail fast on failure."""
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))
    except Exception as e:
        raise RuntimeError(f'Database connectivity check failed: {e}') from e
    finally:
        db.close()

    storage = LocalAudioStorage()
    storage.validate_writable()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        validate_startup_resources()
    except Exception:
        logger.warning('Startup resource validation failed', exc_info=True)
        logger.warning(
            'The API will start, but the /health endpoint will report '
            'the actual status of each dependency.'
        )
    yield


app = FastAPI(
    title='Audio Transcription API',
    version='0.1.0',
    description='Internal REST API for asynchronous audio transcription '
    'using Faster Whisper.',
    lifespan=lifespan,
)

app.include_router(transcriptions_router)
app.include_router(health_router)
