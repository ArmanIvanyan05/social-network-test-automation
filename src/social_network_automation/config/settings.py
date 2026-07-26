"""Environment-driven framework settings."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BrowserName(StrEnum):
    """Browsers supported by Playwright fixtures."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class Settings(BaseSettings):
    """Validated settings shared by tests and framework services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AUTOMATION_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "local"
    frontend_url: AnyHttpUrl = AnyHttpUrl("http://localhost:5173")
    api_url: AnyHttpUrl = AnyHttpUrl("http://localhost:4002/api")
    browser: BrowserName = BrowserName.CHROMIUM
    headless: bool = True
    slow_mo_ms: int = Field(default=0, ge=0)
    ui_timeout_ms: int = Field(default=10_000, gt=0)
    api_timeout_seconds: float = Field(default=10.0, gt=0)
    ignore_https_errors: bool = False
    cors_proxy: bool = False
    artifacts_dir: Path = Path("artifacts")

    @property
    def frontend_base_url(self) -> str:
        """Return the frontend URL without a trailing slash."""
        return str(self.frontend_url).rstrip("/")

    @property
    def api_base_url(self) -> str:
        """Return the API URL without a trailing slash."""
        return str(self.api_url).rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache the process configuration."""
    return Settings()
