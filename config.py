"""Application configuration helpers."""

import os
from typing import Dict, Optional

import dotenv

dotenv.load_dotenv()


class Settings:
    """Centralised configuration for the FastAPI application."""

    def __init__(self) -> None:
        self.openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url: str = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.openrouter_app_url: Optional[str] = os.getenv("OPENROUTER_APP_URL")
        self.openrouter_app_title: Optional[str] = os.getenv("OPENROUTER_APP_TITLE")
        self.default_model: str = os.getenv("DEFAULT_MODEL", "openrouter/auto")
        self.default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    def validate(self) -> bool:
        """Return ``True`` when a valid OpenRouter configuration is present."""

        if not self.openrouter_api_key:
            return False
        if self.openrouter_api_key == "your-openrouter-api-key-here":
            return False
        return True

    def get_model_config(self, model_name: Optional[str] = None) -> Dict[str, object]:
        """Return the configuration required to create an LLM client."""

        headers: Dict[str, str] = {}
        if self.openrouter_app_url:
            headers["HTTP-Referer"] = self.openrouter_app_url
        if self.openrouter_app_title:
            headers["X-Title"] = self.openrouter_app_title

        return {
            "model": model_name or self.default_model,
            "temperature": self.default_temperature,
            "openai_api_key": self.openrouter_api_key,
            "openai_api_base": self.openrouter_base_url,
            "default_headers": headers,
        }


# Global settings instance
settings = Settings()
