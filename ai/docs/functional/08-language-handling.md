# Functional — Language Handling

> Source: `functional-specification.md` §6

The upload endpoint accepts an optional `language` field.

Example:

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions \
  -F 'audio=@sample.mp3' \
  -F 'language=pt'
```

## 6.1 Language Validation

The `language` value must be a simple ISO-like lowercase language code.

Accepted pattern:

```regex
^[a-z]{2,5}$
```

Examples:

- `pt`
- `en`
- `es`
- `fr`

The API does not maintain a full allowlist of supported languages in v1.

Invalid language values should be rejected at upload time.

## 6.2 Language Storage Behavior

The job uses a single `language` field.

If the client provides a language, the job stores that value.

If the client does not provide a language, the job initially stores `null`.

When Faster Whisper auto-detects the language, the worker stores the detected language in the same field.

Examples:

```text
Client sends language=pt
→ job.language starts as pt
→ worker keeps language as pt

Client omits language
→ job.language starts as null
→ worker stores detected language, for example pt
```
