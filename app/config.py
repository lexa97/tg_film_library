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
    
    # Prowlarr API
    prowlarr_url: str
    prowlarr_api_key: str
    
    # Download Group ID (group that can auto-download via Prowlarr)
    # Other groups will receive torrent files instead
    download_group_id: int | None = None
    
    # Proxy (опционально, для обхода блокировок)
    # Формат: http://user:pass@host:port или socks5://host:port
    proxy_url: str | None = None
    
    # Database
    database_url: str
    
    # Pagination
    films_per_page: int = 10

    # Кэш TMDB recommendations (/relative): интервалы и пауза между запросами к API.
    # Запуск цикла — app.main.recommendation_cache_background_loop;
    # наполнение таблицы film_recommendation_cache —
    # app.services.recommendation_refresh.refresh_recommendation_cache_for_all_sources.
    recommendation_cache_interval_hours: float = 24.0
    recommendation_initial_delay_sec: float = 60.0
    recommendation_tmdb_delay_sec: float = 0.35


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
