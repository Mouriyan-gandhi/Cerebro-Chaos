"""
Cerebro Chaos - Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://cerebro:cerebro@localhost:5432/cerebro_chaos"
    
    # LLM
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    
    # GitHub
    GITHUB_TOKEN: str = ""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Repos
    REPOS_DIR: str = str(Path(__file__).parent / "repos")
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
os.makedirs(settings.REPOS_DIR, exist_ok=True)
