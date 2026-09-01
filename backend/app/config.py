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
    database_url: str = "sqlite:///./risk_radar.db"
    api_base_url: str = "http://localhost:8000"
    rss_queries: list[str] = DEFAULT_RSS_QUERIES
    rss_feeds: list[str] = []

settings = Settings()
