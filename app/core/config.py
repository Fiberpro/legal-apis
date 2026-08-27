from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    # --- Odoo principal (FiberPro / Lima) -------------------------------
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USER: str
    ODOO_PASSWORD: str
    # --- Odoo secundario (MaxPro / Chincha - Pisco) ---------------------
    # Si tu despliegue no usa la segunda instancia, puedes omitirlas del .env;
    # la inicialización del cliente se validará al primer uso.
    ODOO_URL_2: Optional[str] = None
    ODOO_DB_2: Optional[str] = None
    ODOO_USER_2: Optional[str] = None
    ODOO_PASSWORD_2: Optional[str] = None
    # --- Proveedor de correo: SendGrid (transaccional) ------------------
    # El backend envía usando SendGrid como proveedor principal.
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: Optional[str] = None  # remitente verificado en SendGrid
    # --- SMTP (legacy / fallback opcional) -------------------------------
    # El proyecto todavía referencia MAIL_USERNAME en algunas rutas
    # (p. ej. fallback SMTP en `odoo_client.send_smtp_email` y como
    # remitente en `email_service.send_legal_email`). Se conserva para
    # no romper compatibilidad, pero el envío real va por SendGrid.
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_USE_TLS: Optional[bool] = None
    MAIL_USE_SSL: Optional[bool] = None
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    # --- Copia interna obligatoria ---------------------------------------
    # MAIL_RECEPTOR recibe siempre una copia del correo para registro
    # interno, independientemente de si el usuario autorizó el envío.
    MAIL_RECEPTOR: Optional[str] = None
    # --- Cuentas específicas MaxPro (legacy) ----------------------------
    MAIL_USERNAME_MP: Optional[str] = None
    MAIL_PASSWORD_MP: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
settings = Settings()