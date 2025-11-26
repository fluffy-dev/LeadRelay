from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration."""
    DATABASE_URL: str = "sqlite+aiosqlite:///./crm.db"
    TITLE: str = "Mini-CRM Lead Distributor"

settings = Settings()