from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "production", "test"] = "development"
    secret_key: str = "dev-secret"
    api_v1_prefix: str = "/api/v1"
    groq_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://tutor:tutor@localhost:5432/tutor_db"
    sync_database_url: str = "postgresql://tutor:tutor@localhost:5432/tutor_db"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # Defaults
    default_subject: str = "pure_mathematics"
    default_exam_board: str = "edexcel"

    # Auth
    access_token_expire_minutes: int = 60

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()