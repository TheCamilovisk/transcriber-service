"""Worker entrypoint: polling loop for audio transcription jobs."""

from __future__ import annotations

import logging
import signal
import sys
import time

from sqlalchemy import text

from app.application.services.transcription_service import (
    TranscriptionService,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.storage.local_audio_storage import LocalAudioStorage
from app.infrastructure.transcriber.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
)
from app.settings import get_settings

logger = logging.getLogger(__name__)

_shutdown_requested = False


def _handle_signal(signum: int, frame) -> None:
    global _shutdown_requested  # noqa: PLW0603
    logger.info('Worker shutdown requested (signal %d).', signum)
    _shutdown_requested = True


def _configure_logging(settings) -> None:
    log_level = getattr(settings, 'log_level', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout,
    )


def _validate_database() -> None:
    """Validate database connectivity. Fail fast on failure."""
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))
        logger.info('Database connectivity validated.')
    except Exception as e:
        raise RuntimeError(f'Database connectivity check failed: {e}') from e
    finally:
        db.close()


def _ensure_upload_dir(settings) -> None:
    """Ensure upload directory exists and is writable."""
    storage = LocalAudioStorage()
    storage.validate_writable()
    logger.info('Upload directory validated: %s', settings.upload_dir)


def _reset_processing_jobs() -> None:
    """Reset jobs stuck in 'processing' back to 'pending' on startup."""
    db = SessionLocal()
    try:
        service = TranscriptionService(db)
        jobs = service.reset_processing_jobs_to_pending()
        if jobs:
            logger.info(
                'Reset %d stuck processing job(s) to pending.',
                len(jobs),
            )
        else:
            logger.info('No stuck processing jobs to reset.')
    finally:
        db.close()


def run_polling_loop(transcriber: FasterWhisperTranscriber) -> None:
    """Main polling loop — claim and process jobs until shutdown."""
    settings = get_settings()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info('Worker polling loop started.')

    while not _shutdown_requested:
        db = SessionLocal()
        try:
            service = TranscriptionService(db)

            if _shutdown_requested:
                break

            job = service.claim_next_pending_job()

            if job is None:
                logger.info(
                    'Waiting for jobs (poll interval: %ds).',
                    settings.worker_poll_interval_seconds,
                )
                # Release DB connection before sleeping.
                db.close()
                db = None
                _wait_with_shutdown_check(settings.worker_poll_interval_seconds)
                continue

            logger.info('Claimed job id=%s.', job.id)
            logger.info('Started transcription job id=%s.', job.id)

            service.process_job(job.id, transcriber)

            logger.info('Completed job id=%s.', job.id)

        finally:
            if db is not None:
                db.close()

    logger.info('Worker shutdown complete.')


def _wait_with_shutdown_check(interval_seconds: int) -> None:
    """Sleep in short increments so shutdown is responsive."""
    for _ in range(interval_seconds):
        if _shutdown_requested:
            break
        time.sleep(1)


def main() -> None:
    settings = get_settings()
    _configure_logging(settings)

    logger.info('Worker starting.')

    # 1. Validate database connectivity.
    _validate_database()

    # 2. Ensure upload directory exists and is writable.
    _ensure_upload_dir(settings)

    # 3. Reset stuck processing jobs to pending.
    _reset_processing_jobs()

    # 4. Create Faster Whisper transcriber.
    logger.info(
        'Loading Faster Whisper model (size=%s, device=%s, compute_type=%s).',
        settings.faster_whisper_model_size,
        settings.faster_whisper_device,
        settings.faster_whisper_compute_type,
    )
    transcriber = FasterWhisperTranscriber(
        model_size=settings.faster_whisper_model_size,
        device=settings.faster_whisper_device,
        compute_type=settings.faster_whisper_compute_type,
    )
    logger.info('Faster Whisper model loaded.')

    # 5. Enter polling loop.
    run_polling_loop(transcriber)


if __name__ == '__main__':
    main()
