"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ANTHROPIC_API_KEY: str

    # JWT settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # Email settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@tristatebids.com"

    # App settings
    APP_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
