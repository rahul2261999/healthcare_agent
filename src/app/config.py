from __future__ import annotations
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

"""Central application configuration.

This module defines a single `Settings` class (Pydantic v2) that reads
environment variables from both the process environment and a local
`.env` file.  Access it via `get_settings()` which returns a cached
instance.
"""


class Settings(BaseSettings):
    """Runtime configuration for the entire application."""

    # ---------------------------------------------------------------------
    # Core service
    # ---------------------------------------------------------------------
    port: int = Field(
        8000, description="Port the FastAPI server binds to", alias="PORT"
    )

    reload_on_startup: bool = Field(
        False,
        description="Whether Uvicorn reloads on file changes (dev only)",
        alias="RELOAD_ON_STARTUP",
    )

    # Base host used when constructing public URLs (e.g., ngrok host)
    app_base_host: str = Field("localhost:8000", alias="APP_BASE_HOST")


    # ---------------------------------------------------------------------
    # Logging levels
    # ---------------------------------------------------------------------
    log_console_level: str = Field("INFO", alias="LOG_CONSOLE_LEVEL")
    log_file_level: str = Field("DEBUG", alias="LOG_FILE_LEVEL")

    # ------------------------------------------------------------------
    # Pydantic settings
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Derived helpers (not env-driven)
    # ------------------------------------------------------------------
    @property
    def public_host(self) -> str:  # noqa: D401 – simple helper
        """Return externally reachable host (domain:port)."""
        return self.app_base_host

    @property
    def websocket_url(self) -> str:  # noqa: D401 – simple helper
        """Return the Conversation Relay websocket URL.

        Preference order:
        1. VOICE_WEBSOCKET_URL if provided
        2. wss://<public_host>/voice/ws (derived)
        """

        return f"wss://{self.app_base_host}/voice/ws"


# Cached accessor -----------------------------------------------------------


@lru_cache
def get_settings() -> Settings:  # noqa: D401 – simple helper
    """Return a cached Settings instance (singleton style)."""

    return Settings()  # type: ignore[call-arg]
