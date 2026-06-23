from enum import StrEnum


class TranscriptionJobStatus(StrEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
