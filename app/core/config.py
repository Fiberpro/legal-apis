from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USER: str
    ODOO_PASSWORD: str

    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env",extra="ignore", env_file_encoding="utf-8")

settings = Settings()
