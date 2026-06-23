# Functional — Purpose and Product Scope

> Source: `functional-specification.md` §1–2

## 1. Purpose

The **Audio Transcription API** is an internal REST API for asynchronous transcription of audio files using **Faster Whisper**.

The API receives an audio file from a trusted backend service or local/internal script, creates a transcription job, and returns the job information immediately. A separate worker process later processes the job and stores the transcription result. Clients fetch the job status and result by polling the API.

This specification defines the functional behavior of the application.

## 2. Product Scope

### 2.1 Intended Clients

The API is intended for:

- Other backend services
- Internal/local scripts

It is not primarily designed for a browser frontend, mobile app, or public external consumers.

### 2.2 Exposure Model

The API is **internal-only** in version 1.

It is assumed to run in a trusted private environment, such as:

- Local machine
- Private development environment
- Internal network
- Private service-to-service setup

The API must not be exposed publicly without adding authentication and other hardening measures.

### 2.3 Authentication

Version 1 has **no authentication**.

This is acceptable only because the service is internal-only.

Future versions may add API key authentication if the service becomes remotely accessible or exposed to additional trusted services.
