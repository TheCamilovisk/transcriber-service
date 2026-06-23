# Functional — Core User Flow

> Source: `functional-specification.md` §3

The transcription flow is always asynchronous.

1. Client uploads an audio file to the API.
2. API validates the file.
3. API stores the uploaded audio temporarily.
4. API creates a transcription job with status `pending`.
5. API returns the created job immediately.
6. Worker polls for pending jobs.
7. Worker claims the oldest pending job.
8. Worker transcribes the audio using Faster Whisper.
9. Worker stores the transcription result in the database.
10. Worker deletes the original uploaded audio file.
11. Client polls the API to fetch job status and result.

The API does not support synchronous transcription in v1.

The API does not support webhooks or callbacks in v1.

Clients are expected to poll the job endpoint.
