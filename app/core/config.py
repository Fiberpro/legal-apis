from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USER: str
    ODOO_PASSWORD: str 

    model_config = SettingsConfigDict(env_file=".env",extra="ignore", env_file_encoding="utf-8")

settings = Settings()