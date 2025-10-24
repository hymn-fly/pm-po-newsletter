from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field, HttpUrl


class Settings(BaseSettings):
    supabase_url: HttpUrl = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str | None = Field(None, env="SUPABASE_ANON_KEY")
    allowed_origins: List[str] = Field(default_factory=list, env="ALLOWED_ORIGINS")

    mailie_api_base_url: HttpUrl = Field(..., env="MAILIE_API_BASE_URL")
    mailie_api_key: str = Field(..., env="MAILIE_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
