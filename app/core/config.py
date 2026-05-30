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
    default_subject: str = "mathematics"
    default_exam_board: str = "edexcel"

    # Auth
    access_token_expire_minutes: int = 60

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Stripe (set in production .env)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""

    # Frontend URL (used for Stripe redirect URLs)
    frontend_url: str = "https://ascend-tutor-ai-agent.netlify.app"

    # Rate limiting
    free_daily_message_limit: int = 20

    # Sentry
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()