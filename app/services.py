# app/services.py
import smtplib
import os
import xmlrpc.client
from email.message import EmailMessage
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USER: str
    ODOO_PASSWORD: str
    
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_RECEPTOR: str

    model_config = SettingsConfigDict(env_file=".env",extra="ignore", env_file_encoding="utf-8")

settings = Settings()

# --- Conexión XML-RPC con Odoo ---
class OdooClient:
    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self._uid = None
        self._common = None
        self._models = None

    @property
    def common(self):
        if not self._common:
            self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        return self._common

    @property
    def models(self):
        if not self._models:
            self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return self._models

    def authenticate(self):
        if not self._uid:
            self._uid = self.common.authenticate(self.db, self.username, self.password, {})
        return self._uid

    def execute_kw(self, model: str, method: str, args: list = None, kwargs: dict = None):
        uid = self.authenticate()
        return self.models.execute_kw(
            self.db, uid, self.password, model, method, args or [], kwargs or {}
        )

odoo = OdooClient()

# --- Envío de Correos con PDF Adjunto ---
def enviar_correo_con_pdf(destinatario: str, asunto: str, cuerpo: str, ruta_pdf: str, nombre_adjunto: str = "Libro_de_Reclamaciones.pdf"):
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = destinatario
    msg.set_content(cuerpo)

    # Adjuntar archivo
    with open(ruta_pdf, "rb") as f:
        contenido_pdf = f.read()
        msg.add_attachment(
            contenido_pdf,
            maintype="application",
            subtype="pdf",
            filename=nombre_adjunto
        )

    # Enviar por SMTP
    if settings.MAIL_USE_SSL:
        with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            if settings.MAIL_USE_TLS:
                server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)