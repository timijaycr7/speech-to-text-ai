from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STT_",
        extra="ignore",
    )

    model_name: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str | None = "en"
    beam_size: int = 5
    log_level: str = "INFO"
    max_upload_size_mb: int = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()
