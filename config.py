"""
Configuration Management Module
"""
import os
from typing import Optional
import dotenv
dotenv.load_dotenv()

class Settings:
    """Application Configuration Class"""
    
    def __init__(self):
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        self.default_model: str = os.getenv("DEFAULT_MODEL", "google/gemma-2-9b-it:free")
        self.default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    def validate(self) -> bool:
        """Validate if configuration is valid"""
        if not self.openai_api_key:
            return False
        if self.openai_api_key in ["your-openai-api-key-here", "your-openrouter-api-key-here"]:
            return False
        return True
    
    def get_model_config(self, model_name: Optional[str] = None) -> dict:
        """Get model configuration"""
        return {
            "model": model_name or self.default_model,
            "temperature": self.default_temperature,
            "openai_api_key": self.openai_api_key,
            "openai_api_base": self.openai_base_url
        }


# Global configuration instance
settings = Settings()
