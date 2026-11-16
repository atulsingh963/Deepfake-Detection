import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "MINO Deepfake Forensics"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "mino-dev-secret-key-replace-in-production-at-least-32-chars-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./mino.db"

    # Redis & Workers
    REDIS_URL: str = "redis://localhost:6379/0"
    TASK_QUEUE_NAME: str = "mino_analysis_queue"
    WORKER_MODE: str = "inprocess"  # 'inprocess' or 'redis'

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./data/storage"
    LOCAL_UPLOAD_DIR: str = "./data/uploads"

    # Superuser seed
    FIRST_SUPERUSER_EMAIL: str = "admin@mino.local"
    FIRST_SUPERUSER_PASSWORD: str = "AdminSecurePassword123!"
    FIRST_SUPERUSER_NAME: str = "System Administrator"

    # Media limits
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB
    MAX_VIDEO_DURATION_SECONDS: int = 180           # 3 minutes
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "mov", "webm"]

    # ML parameters
    DEVICE: str = "cpu"
    DEFAULT_MODEL_NAME: str = "mino-efficientnet-b0"
    DEFAULT_MODEL_VERSION: str = "v1.0.0"
    MODEL_CHECKPOINT_PATH: str = "./data/models/mino_baseline_v1.pt"
    VIDEO_SAMPLE_FRAMES: int = 16
    SCORE_THRESHOLD_LOW: float = 0.35
    SCORE_THRESHOLD_HIGH: float = 0.65

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
