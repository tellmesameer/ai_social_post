# backend\config.py

# Standard library imports
from pathlib import Path
from typing import Optional

# Third-party imports
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Explicitly load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # App settings
    app_name: str = "AI Social Post Generator"
    debug: bool = True
    
    # Directory settings
    base_dir: Path = Path(__file__).parent.parent
    tmp_dir: Path = base_dir / "tmp"
    
    # Database settings
    database_url: str = "sqlite:///./ai_social_posts.db"
    
    # Vertex AI settings
    # Make API key optional so the app can run without it in dev; presence will enable Vertex usage.
    google_api_key: Optional[str] = None
    google_application_credentials: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: str = "us-central1"
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    
    # LinkedIn settings
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    
    # Provider settings
    primary_provider: str = "vertex"
    enable_fallback: bool = True
    
    # API settings
    api_base_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure tmp directory exists
settings.tmp_dir.mkdir(exist_ok=True)