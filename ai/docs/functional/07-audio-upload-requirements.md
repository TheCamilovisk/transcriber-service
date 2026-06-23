# Functional — Audio Upload Requirements

> Source: `functional-specification.md` §5

## 5.1 Accepted Formats

Version 1 must accept the following file extensions:

- `mp3`
- `wav`
- `m4a`
- `ogg`
- `webm`

The API performs light validation based on:

- File extension
- File size
- Empty file check

The worker/transcriber performs deeper validation during decoding/transcription.

## 5.2 Maximum File Size

The maximum upload size is:

```text
25 MB
```

If the uploaded file exceeds this limit, the API must return:

```http
413 Payload Too Large
```

Example response:

```json
{
  "detail": "Uploaded audio file exceeds the 25 MB limit."
}
```

## 5.3 Empty File

If the uploaded file is empty, the API must return:

```http
400 Bad Request
```

Example response:

```json
{
  "detail": "Uploaded audio file is empty."
}
```

`file_size_bytes` and the empty-file check are both based on the number of bytes actually written to disk during `save_upload`, never on a client-supplied `Content-Length` header. This keeps both checks consistent and not spoofable via headers.

## 5.4 Unsupported Format

If the file extension is unsupported, the API must return:

```http
400 Bad Request
```

Example response:

```json
{
  "detail": "Unsupported audio format. Allowed formats: mp3, wav, m4a, ogg, webm."
}
```

### 5.4.1 Extension Extraction Rule

The extension is extracted as the last suffix of the original filename, compared case-insensitively against the allowed list:

- `meeting.MP3` → extension `mp3` (lowercased) → accepted.
- `meeting` (no extension) → unsupported format → rejected.
- `meeting.mp3.exe` → extension `exe` (last suffix only) → rejected.

The stored filename (`{job_id}.{extension}`) always uses the lowercased extension, regardless of the case the client sent.

## 5.5 Content Type

The API should store the uploaded file content type when provided by the client.

The API must not require content type.

The API must not validate content type against a strict allowlist in v1.

A job may have:

```json
{
  "content_type": "audio/mpeg"
}
```

or:

```json
{
  "content_type": null
}
```

## 5.6 Duration Limit

Version 1 has no explicit audio duration limit.

Only the 25 MB file size limit is enforced.
