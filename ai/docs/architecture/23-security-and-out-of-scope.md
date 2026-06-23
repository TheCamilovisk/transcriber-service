# Architecture — Security and Out-of-Scope Architecture

> Source: `architecture-specification.md` §32–33

## 32. Security Architecture

Version 1 has no authentication because it is internal-only.

Security assumptions:

- Service runs only in trusted private environments
- Service is not exposed publicly
- Clients are trusted backend services or local scripts

The architecture must not imply this API is safe for public exposure.

Before public exposure, the system would need:

- Authentication
- Authorization
- Request limits
- Stricter upload validation
- Possibly API keys
- Deployment hardening

## 33. Out-of-Scope Architecture

The v1 architecture intentionally excludes:

- Redis
- Celery
- RQ
- Dramatiq
- PostgreSQL
- S3/object storage
- Multiple workers
- Worker concurrency
- Webhooks
- Authentication
- User accounts
- Metrics endpoint
- Prometheus
- OpenTelemetry
- Worker heartbeat
- Worker HTTP server
- Full hexagonal architecture
- Generic repository interfaces
- Generic storage interfaces
- Generic transcriber interfaces

These can be introduced later if the project grows.
