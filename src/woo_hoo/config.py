"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables can be set directly or via a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM API Key (used for whichever provider is selected)
    llm_api_key: str = Field(
        "",
        description="API key for the selected LLM provider (OpenRouter, Anthropic, or custom)",
    )
    default_model: str = Field(
        "mistralai/mistral-large-2512",
        description="Default LLM model (EU-based Mistral preferred for Dutch govt data sovereignty)",
    )
    fallback_model: str = Field(
        "mistralai/mistral-small-3.2-24b-instruct-2506",
        description="Fallback model if primary fails (also EU-based)",
    )

    # Application
    app_name: str = Field("woo-hoo", description="Application name")
    app_url: str = Field(
        "http://localhost:8000",
        description="Application URL (used for OpenRouter attribution)",
    )
    debug: bool = Field(False, description="Debug mode")

    # Logging
    log_level: str = Field("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    log_format: str = Field("json", description="Log format (json or console)")

    # LLM settings
    max_text_length: int = Field(
        15000,
        description="Maximum document text length to send to LLM",
    )
    llm_timeout_seconds: int = Field(60, description="Timeout for LLM requests in seconds")
    llm_max_retries: int = Field(3, description="Maximum retry attempts for LLM requests")
    llm_temperature: float = Field(0.1, description="Default sampling temperature")

    # LLM Provider Settings
    llm_provider: str = Field(
        "openrouter",
        description="LLM provider: 'openrouter', 'anthropic', or 'custom'",
    )
    anthropic_base_url: str = Field(
        "https://api.anthropic.com",
        description="Anthropic API base URL (override for proxies)",
    )
    custom_llm_base_url: str = Field(
        "",
        description="Custom LLM base URL (e.g., http://ollama:11434/v1)",
    )

    # Optional GPP integration
    gpp_publicatiebank_url: str | None = Field(
        None,
        description="GPP-publicatiebank API URL (optional for integration)",
    )
    gpp_api_token: str | None = Field(
        None,
        description="GPP API token for authentication",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
