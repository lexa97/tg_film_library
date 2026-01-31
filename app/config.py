"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.
    
    Parameters are loaded first from .env file, then from environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Bot
    bot_token: str
    
    # TMDB API
    tmdb_api_key: str
    
    # Database
    database_url: str
    
    # Pagination
    films_per_page: int = 10


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
