from fastapi import FastAPI

from app.api.routes.transcriptions import router as transcriptions_router

app = FastAPI(
    title='Audio Transcription API',
    version='0.1.0',
    description='Internal REST API for asynchronous audio transcription '
    'using Faster Whisper.',
)

app.include_router(transcriptions_router)
