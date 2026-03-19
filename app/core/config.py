import json
from functools import lru_cache
from typing import Any, List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(..., validation_alias="APP_NAME")
    app_version: str = Field(..., validation_alias="APP_VERSION")
    environment: str = Field(..., validation_alias="ENVIRONMENT")
    debug: bool = Field(..., validation_alias="DEBUG")
    api_prefix: str = Field(..., validation_alias="API_PREFIX")
    api_version: str = Field(..., validation_alias="API_VERSION")

    database_url: str = Field(..., validation_alias="DATABASE_URL")

    tmdb_api_key: str = Field(..., min_length=1, validation_alias="TMDB_API_KEY")
    tmdb_base_url: AnyHttpUrl = Field(..., validation_alias="TMDB_BASE_URL")
    tmdb_image_base_url: AnyHttpUrl = Field(
        ...,
        validation_alias="TMDB_IMAGE_BASE_URL",
    )

    cors_origins: List[str] = Field(
        ...,
        validation_alias="CORS_ORIGINS",
    )

    default_page_size: int = Field(..., validation_alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(..., validation_alias="MAX_PAGE_SIZE")

    # Rate limits use SlowAPI syntax.
    default_rate_limit: str = Field(..., validation_alias="DEFAULT_RATE_LIMIT")
    search_rate_limit: str = Field(..., validation_alias="SEARCH_RATE_LIMIT")
    detail_rate_limit: str = Field(..., validation_alias="DETAIL_RATE_LIMIT")

    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> List[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        raise ValueError("Invalid CORS_ORIGINS format")

    @field_validator("api_prefix", mode="before")
    @classmethod
    def normalize_api_prefix(cls, value: Any) -> str:
        raw = str(value).strip() if value is not None else ""
        if not raw:
            raise ValueError("API_PREFIX cannot be empty")
        normalized = raw if raw.startswith("/") else f"/{raw}"
        normalized = normalized.rstrip("/")
        if not normalized:
            raise ValueError("API_PREFIX cannot be root only")
        return normalized

    @field_validator("api_version", mode="before")
    @classmethod
    def normalize_api_version(cls, value: Any) -> str:
        raw = str(value).strip() if value is not None else ""
        normalized = raw.strip("/")
        if not normalized:
            raise ValueError("API_VERSION cannot be empty")
        return normalized

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()