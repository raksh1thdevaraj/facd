import json
from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Metadata
    APP_NAME: str = "AI Certificate Verification Engine"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Server Bindings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Security
    SECRET_KEY: str = "default-insecure-dev-key-change-in-production-0123456789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"
    DB_ECHO: bool = False

    # Asynchronous Task Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_ASYNC_CELERY: bool = False

    # File Storage Paths
    STORAGE_BASE_DIR: Path = Path("./storage")
    UPLOAD_DIR: Path = Path("./storage/uploads")
    PREPROCESSED_DIR: Path = Path("./storage/preprocessed")
    REPORT_DIR: Path = Path("./storage/reports")
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # OCR Configuration
    OCR_ENGINE: str = "easyocr"
    OCR_LANGUAGES: str = "en"
    TESSERACT_CMD: str = "tesseract"

    # Machine Learning / Deep Learning
    MODEL_DIR: Path = Path("./ml/models")
    MODEL_VERSION: str = "v1.0"
    DEVICE: str = "cpu"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def normalize_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def ensure_directories_exist(self) -> None:
        """Ensure all required runtime storage directories exist."""
        for path in [
            self.STORAGE_BASE_DIR,
            self.UPLOAD_DIR,
            self.PREPROCESSED_DIR,
            self.REPORT_DIR,
            self.MODEL_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories_exist()
