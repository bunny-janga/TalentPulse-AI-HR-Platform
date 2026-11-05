import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "TalentPulse AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    # Leave empty to auto-generate a random key on first run (stored in data/.secret_key, git-ignored).
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database (SQLite by default, works with Postgres/MySQL)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'talentpulse.db'}"
    
    # AI & ML
    MODEL_DIR: str = str(BASE_DIR / "data" / "models")
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "policies")
    
    # GenAI
    LLM_PROVIDER: str = "gemini"  # gemini, groq, openai
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 20

    # Demo + hardening
    DEMO_MODE: bool = True            # re-hash the 5 documented demo logins at startup; set false in production
    CORS_ORIGINS: str = "http://localhost:5000,http://127.0.0.1:5000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
    MAX_UPLOAD_MB: int = 8

    class Config:
        env_file = (str(BASE_DIR / ".env"), ".env")
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()

if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
    import secrets
    _key_file = BASE_DIR / "data" / ".secret_key"
    _key_file.parent.mkdir(parents=True, exist_ok=True)
    if _key_file.exists() and len(_key_file.read_text().strip()) >= 32:
        settings.SECRET_KEY = _key_file.read_text().strip()
    else:
        settings.SECRET_KEY = secrets.token_urlsafe(48)
        _key_file.write_text(settings.SECRET_KEY)

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.MODEL_DIR).mkdir(parents=True, exist_ok=True)
