"""Root test configuration — loaded before any test module.

Ensures environment variables from the project .env file (Docker paths)
do not leak into Settings during test imports.  We overwrite the known
interfering keys at module level so that pydantic-settings picks up the
canonical code defaults (env vars take precedence over .env file values).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Override .env variables with code defaults so tests are hermetic.
# Environment variables take priority over .env in pydantic-settings,
# but we must set them *before* any test module triggers a Settings()
# construction (e.g. via from app.main import app).
# ---------------------------------------------------------------------------
os.environ.setdefault('DATABASE_URL', 'sqlite:///./data/app.db')
os.environ.setdefault('UPLOAD_DIR', './data/uploads')
