from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Ecommerce AI Assistant"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENABLE_DOCS: bool = True
    ENABLE_DEMO_MODE: bool = True

    API_KEY: str
    BASE_URL: str
    SEEDREAM_IMAGE_URL: str

    MULTIMODAL_MODEL: str
    DEEPSEEK_MODEL: str
    SEEDREAM_IMAGE_MODEL: str

    REDIS_URL: str
    DATABASE_URL: str = "mysql+aiomysql://root:root@localhost:3306/ecommerce_ai_db"

    MAX_RAW_IMAGE_BYTES: int = 8 * 1024 * 1024
    MAX_CONCURRENT_IMAGE_GEN: int = 3
    TASK_RESULT_CACHE_TTL: int = 30

    TASK_TIME_LIMIT: int = 600
    TASK_SOFT_TIME_LIMIT: int = 540
    TASK_DEFAULT_RETRY_DELAY: int = 60
    TASK_MAX_RETRIES: int = 3
    TASK_ACKS_LATE: bool = True
    TASK_REJECT_ON_WORKER_LOST: bool = True
    RESULT_EXPIRES: int = 3600
    WORKER_PREFETCH_MULTIPLIER: int = 1

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DEMO_USERNAME: str = "admin"
    DEMO_PASSWORD: str = "123456"

    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def docs_url(self) -> Optional[str]:
        return "/docs" if self.ENABLE_DOCS else None

    @property
    def redoc_url(self) -> Optional[str]:
        return "/redoc" if self.ENABLE_DOCS else None

    @property
    def cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
