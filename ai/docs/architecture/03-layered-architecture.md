# Architecture — Layered Architecture

> Source: `architecture-specification.md` §5

The application uses a simple layered architecture.

```text
API layer
  ↓
Application service layer
  ↓
Repository / storage / transcriber layer
  ↓
SQLite / filesystem / Faster Whisper
```

The worker also uses the application service layer.

```text
Worker entrypoint
  ↓
Application service layer
  ↓
Repository / storage / transcriber layer
  ↓
SQLite / filesystem / Faster Whisper
```

## 5.1 Layer Responsibilities

### API Layer

Responsible for:

- FastAPI routes
- Request parsing
- Response schemas
- HTTP status codes
- Dependency injection

The API layer should not contain business workflow logic.

It should delegate use cases to the application service.

### Application Service Layer

Responsible for:

- Creating jobs
- Validating application-level decisions
- Coordinating file storage and database writes
- Listing jobs
- Fetching jobs
- Claiming jobs
- Processing jobs
- Setting lifecycle timestamps
- Owning database transactions

The service layer owns transaction boundaries.

Repositories do not commit internally.

### Repository Layer

Responsible for:

- SQLAlchemy queries
- Adding job records
- Updating job records
- Listing jobs
- Counting jobs
- Fetching jobs by ID

Repositories receive an active SQLAlchemy session.

Repositories do not create sessions.

Repositories do not commit.

### Storage Layer

Responsible for:

- Creating upload directory
- Validating upload directory writability
- Saving uploaded audio files
- Checking file existence
- Deleting files after processing

The v1 storage implementation is local filesystem only.

### Transcriber Layer

Responsible for:

- Loading Faster Whisper
- Transcribing audio files
- Normalizing transcription text
- Returning text and language result

The v1 transcriber implementation is concrete Faster Whisper integration only.

No generic transcriber interface is required in v1.
