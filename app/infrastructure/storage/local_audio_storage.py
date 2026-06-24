from __future__ import annotations

import logging
from pathlib import Path

from app.settings import get_settings

logger = logging.getLogger(__name__)


class LocalAudioStorage:
    def __init__(self, upload_dir: str | None = None):
        settings = get_settings()
        self._upload_dir = Path(upload_dir or settings.upload_dir)

    def ensure_upload_dir_exists(self) -> None:
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_writable(self) -> None:
        self.ensure_upload_dir_exists()
        test_file = self._upload_dir / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            msg = f'Upload directory is not writable: {e}'
            raise RuntimeError(msg) from e

    def save_upload(
        self, content: bytes, job_id: str, extension: str
    ) -> tuple[str, int]:
        """Save uploaded content and return (stored_path, file_size_bytes)."""
        self.ensure_upload_dir_exists()
        filename = f'{job_id}.{extension}'
        filepath = self._upload_dir / filename
        filepath.write_bytes(content)
        return str(filepath), len(content)

    @staticmethod
    def exists(path: str) -> bool:
        return Path(path).exists()

    @staticmethod
    def delete(path: str) -> None:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as e:
            logger.warning('Failed to delete file %s: %s', path, e)
