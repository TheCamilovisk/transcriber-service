# Architecture — Purpose and Goals

> Source: `architecture-specification.md` §1–2

## 1. Purpose

This document defines the technical architecture for the **Audio Transcription API**.

The system is an internal REST API for asynchronous audio transcription using **FastAPI**, **SQLite**, **local filesystem storage**, and a single **Faster Whisper** worker process.

This architecture intentionally stays simple. It uses a straightforward layered design, not full hexagonal architecture or heavy domain-driven design.

## 2. Architectural Goals

The architecture should optimize for:

- Simplicity
- Clear separation of concerns
- Easy local development
- One-line Docker Compose startup after `.env` exists
- Predictable worker behavior
- Testability without requiring real Faster Whisper in the default test suite
- Future extensibility without overengineering v1

The system should be easy to understand for a developer reading the codebase for the first time.
