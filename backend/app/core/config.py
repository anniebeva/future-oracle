from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables"""

    app_name: str = "Job Market Oracle"
    app_env: str = "development"
    database_url: str
    muse_api_key: str | None = None
    muse_base_url: str = "https://www.themuse.com/api/public"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
