from fastapi import FastAPI

app = FastAPI(
    title='Audio Transcription API',
    version='0.1.0',
    description='Internal REST API for asynchronous audio transcription '
    'using Faster Whisper.',
)
