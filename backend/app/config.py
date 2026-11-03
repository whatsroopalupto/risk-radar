"""Application settings loaded from the environment."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_RSS_QUERIES = ["strait of hormuz oil", "red sea shipping tanker", "crude oil india imports", "oil tanker attack", "iran oil sanctions"]

class Settings(BaseSettings):
    """Keep deployment configuration outside source code."""
    model_config = SettingsConfigDict(env_file=Path(__file__).parents[1] / ".env", extra="ignore")
    gemini_api_key: str = ""
    extractor: str = "auto"
    gemini_model: str = "gemini-3.6-flash"
    database_url: str = "sqlite:///" + (Path(__file__).resolve().parents[2] / "risk_radar.db").as_posix()
    api_base_url: str = "http://localhost:8000"
    rss_queries: list[str] = DEFAULT_RSS_QUERIES
    rss_feeds: list[str] = []
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8501", "http://127.0.0.1:8501"]
    aisstream_api_key: str = ""
    ais_stale_minutes: int = 15
    ais_baseline_days: int = 30
    max_articles_per_run: int = 80

settings = Settings()
