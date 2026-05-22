# app/config.py
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / `.env`.

    pydantic-settings handles env loading natively — no need for a
    separate `load_dotenv()` + `os.getenv()` plumbing. Defaults here are
    safe-for-dev placeholders; production must override.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "Logistics System"
    debug: bool = False

    # ---- Database ----
    db_host: str = "localhost"
    db_port: str = "5432"
    db_user: str = "postgres"
    db_password: str = "change-me"
    db_name: str = "logistics"

    # ---- Telegram ----
    telegram_bot_token: str = ""

    # ---- Auth (JWT) ----
    # SECRET defaults are deliberately bad — meant to fail loudly if anyone
    # ever runs without setting them. Production deployments MUST override
    # via env vars.
    jwt_secret_key: str = "INSECURE-DEV-ONLY-CHANGE-ME"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
