# Architecture — Risks, Constraints, and Acceptance Criteria

> Source: `architecture-specification.md` §34–35

## 34. Architectural Risks and Constraints

### 34.1 SQLite as Queue

SQLite polling is simple and appropriate for v1, but it has limits.

This architecture is suitable for:

- Internal usage
- Low to moderate job volume
- One worker process
- One job at a time

It is not suitable for:

- Many workers
- High throughput
- Distributed processing
- Strong queue guarantees

If those needs appear, migrate to Redis-backed queue or PostgreSQL with locking.

### 34.2 Local Filesystem Storage

Local filesystem storage is simple but requires API and worker to share the same filesystem.

This is handled in Docker Compose with:

```yaml
- ./data:/app/data
```

If API and worker run on different machines later, object storage will be needed.

### 34.3 Faster Whisper Startup Cost

The worker loads Faster Whisper at startup.

This may make worker startup slower.

The benefit is that individual jobs avoid repeated model loading cost.

### 34.4 Python 3.13 Compatibility

The Docker image uses Python 3.13.

If Faster Whisper or related dependencies fail under Python 3.13, the fallback is Python 3.12 slim.

## 35. Acceptance Criteria for Architecture

The architecture is acceptable when:

1. API and worker are separate runtime processes.
2. API and worker share the same application service, repository, settings, database, and storage code.
3. The API route layer remains thin.
4. The service layer owns application workflows and database transactions.
5. The repository layer isolates SQLAlchemy access.
6. The storage class isolates filesystem operations.
7. The transcriber class isolates Faster Whisper integration.
8. SQLite is used for persistence and pending job discovery.
9. The worker polls SQLite and processes one job at a time.
10. Docker Compose can start migration, API, and worker services.
11. API and worker share the same `./data` bind mount.
12. Alembic migrations run before API and worker start in Docker Compose.
13. Tests can run without a real Faster Whisper model.
14. CI runs Ruff and pytest on `main`/`dev` push and pull requests.
15. The design remains simple and avoids unnecessary v1 abstractions.
