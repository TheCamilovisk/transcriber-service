# Functional — Storage and Retention

> Source: `functional-specification.md` §10

## 10.1 Uploaded Audio Storage

Uploaded audio files are stored on the local filesystem.

The API and worker must share the same filesystem path or mounted volume.

The upload directory must be configurable.

Default direct local path:

```env
UPLOAD_DIR=./data/uploads
```

Default Docker path:

```env
UPLOAD_DIR=/app/data/uploads
```

## 10.2 Upload Directory Behavior

On startup, the API and worker should create the upload directory automatically if it does not exist.

Startup should fail only if the directory:

- Cannot be created
- Is not writable

## 10.3 Original Audio Retention

Uploaded audio is temporary.

The worker must delete the original audio file after processing finishes.

This applies to both:

- Completed jobs
- Failed jobs

The job metadata and transcription result remain stored.

## 10.4 Job Retention

Job records and transcription results are kept indefinitely in v1.

There is no automatic deletion of job records.

## 10.5 Duplicate Uploads

Version 1 does not perform duplicate detection.

Every uploaded audio file creates a new transcription job, even if the same audio was uploaded before.
