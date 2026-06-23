# Architecture — High-Level System and Runtime Architecture

> Source: `architecture-specification.md` §3–4

## 3. High-Level System Design

The application has two main runtime processes:

1. **API process**
   - FastAPI application
   - Receives audio uploads
   - Creates transcription jobs
   - Exposes job retrieval/listing endpoints
   - Exposes health check endpoint

2. **Worker process**
   - Loads Faster Whisper model
   - Polls SQLite for pending jobs
   - Processes one job at a time
   - Stores transcription results
   - Deletes uploaded audio files after processing

There is no external queue in v1.

SQLite acts as both:

- The persistence database
- The simple job queue

Local filesystem storage is used for temporary uploaded audio files.

## 4. Runtime Architecture

### 4.1 Runtime Components

```text
Client
  ↓
FastAPI API process
  ↓
SQLite database
  ↓
Polling worker process
  ↓
Faster Whisper
  ↓
SQLite database updated with result
```

The API and worker communicate indirectly through the database.

The API does not call the worker directly.

The worker does not call the API.

### 4.2 Process Responsibilities

#### API Process

The API process is responsible for:

- Receiving HTTP requests
- Validating uploaded audio files
- Saving uploaded audio to local storage
- Creating transcription job records
- Listing transcription jobs
- Fetching transcription jobs by ID
- Exposing application health

The API process does not perform transcription.

#### Worker Process

The worker process is responsible for:

- Loading Faster Whisper at startup
- Resetting stuck processing jobs to pending on startup
- Polling for pending jobs
- Claiming the oldest pending job
- Marking jobs as processing
- Transcribing audio files
- Saving transcription text
- Marking jobs as completed or failed
- Deleting uploaded audio after processing

The worker processes one job at a time.
