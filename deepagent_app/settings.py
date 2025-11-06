# deepagent_app/settings.py
from __future__ import annotations
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    tavily_api_key: str = Field(alias="TAVILY_API_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_model_provider(self) -> None:
        if not (self.anthropic_api_key or self.openai_api_key):
            raise ValidationError.from_exception_data(
                title="SettingsError",
                line_errors=[{
                    "type": "value_error",
                    "loc": ("provider_key",),
                    "msg": "Provide ANTHROPIC_API_KEY or OPENAI_API_KEY",
                    "input": None,
                }],
            )

settings = Settings()
settings.validate_model_provider()
