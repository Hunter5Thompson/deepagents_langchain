"""
Configuration and Environment Management
Handles API keys, certificates, and environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Immutable configuration container."""

    anthropic_api_key: str
    tavily_api_key: str
    cert_path: Optional[str]
    database_url: Optional[str] = None

    @property
    def has_certificate(self) -> bool:
        """Check if certificate is configured and exists."""
        return self.cert_path is not None

    @property
    def has_database(self) -> bool:
        """Check if database is configured."""
        return self.database_url is not None


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""
    pass


def load_config() -> Config:
    """
    Load and validate configuration from environment.
    
    Returns:
        Config: Validated configuration object
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    load_dotenv()
    
    # Get API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    # Validate required keys
    missing = []
    if not anthropic_key:
        missing.append("ANTHROPIC_API_KEY")
    if not tavily_key:
        missing.append("TAVILY_API_KEY")
    
    if missing:
        raise ConfigurationError(
            f"Missing required API keys: {', '.join(missing)}\n"
            "Create a .env file with these keys."
        )
    
    # Get optional certificate path
    default_cert = r"C:\Users\G441822\AgentenStuff\autogen\company_cert.cer"
    cert_path = os.getenv("COMPANY_CERT_PATH", default_cert)
    
    # Validate certificate if path is provided
    if cert_path and not Path(cert_path).exists():
        print(f"⚠️  Certificate not found: {cert_path}")
        print("    Continuing without custom certificate...")
        cert_path = None
    elif cert_path:
        print(f"✅ Certificate loaded: {Path(cert_path).name}")

    # Get optional database URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print(f"✅ Database configured")
    else:
        print("ℹ️  No database configured (optional)")

    return Config(
        anthropic_api_key=anthropic_key,
        tavily_api_key=tavily_key,
        cert_path=cert_path,
        database_url=database_url
    )


def configure_tls_environment(cert_path: Optional[str]) -> None:
    """
    Configure TLS/SSL environment variables for various HTTP libraries.
    
    Args:
        cert_path: Path to certificate file, or None to skip
    """
    if not cert_path:
        return
    
    # For requests library (used by Tavily)
    os.environ["REQUESTS_CA_BUNDLE"] = cert_path
    os.environ["SSL_CERT_FILE"] = cert_path
    os.environ["CURL_CA_BUNDLE"] = cert_path
    
    # For httpx library (used by Anthropic SDK)
    os.environ["HTTPX_CA_BUNDLE"] = cert_path
    
    print(f"🔐 TLS configured with certificate: {Path(cert_path).name}")