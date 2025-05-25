# app/config.py - Updated to handle Telegram bot token from environment
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    app_name: str = "Logistics System"
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Database settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "5115")
    db_name: str = os.getenv("DB_NAME", "logistics")

    # Telegram Bot Configuration
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    class Config:
        env_file = "../.env"


@lru_cache()
def get_settings():
    """
    Returns cached settings instance for better performance.
    """
    return Settings()
