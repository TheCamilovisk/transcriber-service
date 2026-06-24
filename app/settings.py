from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./data/app.db'
    upload_dir: str = './data/uploads'
    max_upload_size_mb: int = 25
    worker_poll_interval_seconds: int = 3

    faster_whisper_model_size: str = 'small'
    faster_whisper_device: str = 'cpu'
    faster_whisper_compute_type: str = 'int8'

    api_host: str = '0.0.0.0'
    api_port: int = 8000

    model_config = SettingsConfigDict(env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
