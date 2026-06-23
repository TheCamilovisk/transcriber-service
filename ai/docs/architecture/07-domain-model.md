# Architecture — Domain Model

> Source: `architecture-specification.md` §9

## 9.1 Status Enum

The application uses a Python enum for job statuses.

Expected location:

```text
app/domain/enums.py
```

Expected enum:

```python
from enum import StrEnum


class TranscriptionJobStatus(StrEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
```

The database stores the enum value as a string.

## 9.2 No Separate Domain Dataclasses

Version 1 does not define separate domain dataclasses for transcription jobs.

The SQLAlchemy model acts as the internal persisted job representation.

Pydantic schemas control API output.
