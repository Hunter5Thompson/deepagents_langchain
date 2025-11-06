from __future__ import annotations
from pydantic import BaseSettings, Field, ValidationError

class Settings(BaseSettings):
    anthropic_api_key: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    model_config = {"extra": "ignore"}

    def validate_model_provider(self) -> None:
        if not (self.anthropic_api_key or self.openai_api_key):
            raise ValidationError("Provide ANTHROPIC_API_KEY or OPENAI_API_KEY")

settings = Settings()
settings.validate_model_provider()
