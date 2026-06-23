# Architecture — Database Architecture

> Source: `architecture-specification.md` §10

## 10.1 Database Engine

Version 1 uses **SQLite**.

Default direct local database URL:

```env
DATABASE_URL=sqlite:///./data/app.db
```

Default Docker database URL:

```env
DATABASE_URL=sqlite:////app/data/app.db
```

The database URL is configurable through environment variables.

## 10.2 SQLAlchemy Style

The application uses SQLAlchemy 2.0 ORM style.

Use:

- `Mapped`
- `mapped_column`
- `select`
- modern `Session` patterns

Do not use SQLModel.

Do not use classic query-style ORM as the default.

## 10.3 Session Management

Database setup lives in:

```text
app/infrastructure/database/session.py
```

Expected responsibilities:

- Create SQLAlchemy engine
- Create sessionmaker
- Expose session dependency/helper

API routes receive database sessions through FastAPI dependency injection.

Worker code creates sessions through the same session factory.

## 10.4 Database Model

The transcription job model lives in:

```text
app/infrastructure/database/models.py
```

Expected table:

```text
transcription_jobs
```

Fields:

- `id`
- `status`
- `original_filename`
- `stored_audio_path`
- `content_type`
- `file_size_bytes`
- `language`
- `text`
- `error_message`
- `created_at`
- `updated_at`
- `started_at`
- `finished_at`

### 10.4.1 Column Types and Lengths

```python
id: Mapped[str] = mapped_column(String(36), primary_key=True)
status: Mapped[str] = mapped_column(String(20), nullable=False)
original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
stored_audio_path: Mapped[str] = mapped_column(String(512), nullable=False)
content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
language: Mapped[str | None] = mapped_column(String(10), nullable=True)
text: Mapped[str | None] = mapped_column(Text, nullable=True)
error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

`file_size_bytes` is always derived from bytes actually written to disk during upload, never from a client-supplied header.

## 10.5 UUID Storage

SQLite stores UUID values as strings.

Database field:

```python
id: Mapped[str] = mapped_column(String(36), primary_key=True)
```

API schemas expose IDs as UUID values.

The service layer converts between `UUID` and `str` where needed.

## 10.6 Indexes

The database should define indexes for the main query patterns.

Required indexes:

- `status`
- `created_at`
- `status + created_at`

These support:

- Worker claiming oldest pending job
- Status-filtered listing
- Newest-first listing

## 10.7 Migrations

The project uses Alembic from the beginning.

Migrations live in:

```text
alembic/
```

The initial migration creates the `transcription_jobs` table and indexes.

Docker Compose runs:

```bash
uv run alembic upgrade head
```

before starting API and worker.

Direct local development also requires:

```bash
uv run alembic upgrade head
```
