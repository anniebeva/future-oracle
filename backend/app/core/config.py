from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Configuration loaded from environment variables"""

    app_name: str = "Job Market Oracle"
    app_env: str = "development"
    database_url: str
    muse_api_key: str | None = None
    muse_base_url: str = "https://www.themuse.com/api/public"
    remotive_base_url: str = "https://remotive.com/api/remote-jobs"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
