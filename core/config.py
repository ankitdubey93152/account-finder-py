from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "OSINT Digital Footprint Analyzer"
    ENV: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./osint.db"
    
    # Request defaults & rate limits
    DEFAULT_TIMEOUT_SECONDS: float = 8.0
    GLOBAL_SCAN_TIMEOUT_SECONDS: float = 60.0
    MAX_CONCURRENT_REQUESTS: int = 10
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OSINT-Analyzer/1.0"
    
    # Optional Third-Party Keys / Feature Flags
    HIBP_API_KEY: str | None = None
    NUMVERIFY_API_KEY: str | None = None

settings = Settings()
