# Architecture — Storage Architecture

> Source: `architecture-specification.md` §12

## 12.1 Storage Implementation

The storage implementation is a concrete class:

```text
LocalAudioStorage
```

Expected location:

```text
app/infrastructure/storage/local_audio_storage.py
```

No generic storage abstraction is required in v1.

## 12.2 Storage Responsibilities

Expected methods:

```python
class LocalAudioStorage:
    def ensure_upload_dir_exists(self) -> None:
        ...

    def validate_writable(self) -> None:
        ...

    def save_upload(...):
        ...

    def exists(self, path: str) -> bool:
        ...

    def delete(self, path: str) -> None:
        ...
```

## 12.3 File Naming

The saved file uses:

```text
{job_id}.{extension}
```

Example:

```text
/app/data/uploads/8f4b2d6e-91b5-4d3a-a36f-78f2f3c1c9a1.mp3
```

The original filename is stored only as metadata.

### 12.3.1 Extension Extraction Rule

The extension is the last suffix of the original filename, extracted case-insensitively (e.g. via `Path(filename).suffix.lower().lstrip('.')`) and compared against the allowed list in lowercase:

- A filename with no extension (`meeting`) is treated as an unsupported format.
- A filename with multiple suffixes (`meeting.mp3.exe`) uses only the last one (`exe`) for validation.
- The stored filename always uses the lowercased extension, regardless of the case the client sent (`AUDIO.MP3` → stored as `{job_id}.mp3`).

## 12.4 Storage Path Configuration

Default Docker path:

```env
UPLOAD_DIR=/app/data/uploads
```

Default local direct path:

```env
UPLOAD_DIR=./data/uploads
```

Both API and worker must use the same configured upload directory.

## 12.5 Cleanup

The worker deletes uploaded audio after both success and failure.

The storage class should make deletion safe:

- Deleting a missing file should not crash final failure handling
- Deletion errors should be logged
