"""Configuration management for BoondManager integration."""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # BoondManager API - JWT Authentication
    boond_user_token: str
    boond_client_token: str
    boond_client_key: str
    boond_base_url: str = "https://api.boondmanager.com/api/v3"
    boond_timeout: int = 30

    # Email Configuration - SMTP (Sending)
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True

    # Email Configuration - IMAP (Receiving)
    imap_host: str
    imap_port: int = 993
    imap_user: str
    imap_password: str

    # Application Configuration
    tax_rate: float = 0.20
    default_payment_terms_days: int = 30
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "development"


# Global config instance
config = Config()
