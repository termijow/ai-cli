"""AI Orders configuration settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "AI Orders Microservice"
    APP_VERSION: str = "1.0.0"
    APP_PORT: int = 3095
    APP_DEBUG: bool = False
    
    # Whisper Configuration
    WHISPER_MODEL: str = "tts models/whisper-large-v3-turbo"  # Use large-v3 for better accuracy
    WHISPER_TASK: str = "transcribe"
    WHISPER_DEVICE: str = "auto"
    WHISPER_CHUNK_SIZE: int = 512
    WHISPER_GZIP: bool = True
    
    # LLM Configuration
    LLM_MODEL: str = "google/gemma-2-9b-it"  # Reasoning capable model
    LLM_TEMP: float = 0.3  # Lower for more structured output
    LLM_MAX_TOKENS: int = 4096
    
    # Fuzzy Matching
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD: float = 0.75
    TOP_K_MATCHES: int = 5
    
    # Product Catalog
    CATALOG_URL: str = ""  # URL to the product catalog
    CATALOG_EMBEDDINGS_URL: str = ""  # URL to fetch catalog embeddings
    
    # Validation
    MIN_ITEMS: int = 1
    MAX_ITEMS: int = 10
    ALLOWED_CURRENCIES: list = ["USD", "EUR", "GBP"]
    
    # Storage
    AUDIO_STORAGE_PATH: str = "/tmp/ai_orders_audio"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
