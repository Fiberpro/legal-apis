# app/services.py
import smtplib
import os
import xmlrpc.client
import logging
from typing import List, Optional, Tuple
from email.message import EmailMessage
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.email_service import send_legal_email as _send_legal_email

logger = logging.getLogger("legal_services")

class Settings(BaseSettings):
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USER: str
    ODOO_PASSWORD: str
    
    ODOO_URL_2: str
    ODOO_DB_2: str
    ODOO_USER_2: str
    ODOO_PASSWORD_2: str
    
    SENDGRID_API_KEY: str
    FROM_EMAIL: str = ""
    
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_RECEPTOR: str
    
    MAIL_USERNAME_MP: str = ""
    MAIL_PASSWORD_MP: str = ""

    model_config = SettingsConfigDict(env_file=".env",extra="ignore", env_file_encoding="utf-8")

settings = Settings()

# --- Conexión XML-RPC con Odoo ---
def send_legal_email(
    recipient: str,
    subject: str,
    body: str,
    pdf_path: Optional[str] = None,
    attachments: Optional[List[Tuple[str, str, bytes]]] = None,
    cc_receptor: bool = True,
    ) -> bool:
    """
    Envía correo vía SendGrid. Wrapper público que delega a app.core.email_service.
    En Digital Ocean el SMTP saliente está bloqueado, por eso SendGrid es obligatorio.
    Args:
        recipient: Correo del usuario (puede estar vacío si no autorizó notificación)
        subject: Asunto del correo
        body: Cuerpo en texto plano
        pdf_path: Ruta al PDF de constancia
        attachments: Lista de tuplas (nombre, mime_type, bytes) de archivos del frontend
        cc_receptor: Si True, envía copia a MAIL_RECEPTOR
    Returns:
        True si SendGrid aceptó el envío (status 2xx), False en caso contrario
    """
    return _send_legal_email(
        recipient=recipient,
        subject=subject,
        body=body,
        pdf_path=pdf_path,
        attachments=attachments,
        cc_receptor=cc_receptor,
    )

# --- Envío de Correos con PDF Adjunto ---
def enviar_correo_con_pdf(destinatario: str, asunto: str, cuerpo: str, ruta_pdf: str, nombre_adjunto: str = "Libro_de_Reclamaciones.pdf")-> bool:
    logger.info("enviar_correo_con_pdf delegando a SendGrid para %s", destinatario)
    return _send_legal_email(
        recipient=destinatario,
        subject=asunto,
        body=cuerpo,
        pdf_path=ruta_pdf,
        cc_receptor=False,
    )

def build_confirmation_email(
    ticket_name: str,
    tipo: str,  # "Reclamo", "Queja", "Apelación"
    nombre: str,
    apellidos: str,
    ) -> Tuple[str, str]:
    """
    Construye asunto y cuerpo del correo de confirmación.
    
    Returns:
        (asunto, cuerpo)
    """
    subject = f"Constancia de {tipo} - FiberPro - {ticket_name}"
    body = (
        f"Estimado(a) {nombre} {apellidos},\n\n"
        f"Su {tipo.lower()} ha sido registrado correctamente en nuestro sistema.\n\n"
        f"Número de ticket: {ticket_name}\n"
        f"Fecha de registro: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"Adjunto a este correo encontrará su constancia en formato PDF.\n\n"
        f"Este es un mensaje automático. Por favor no responda a esta dirección."
    )
    return subject, body

def build_libro_email(ticket_name: str, sede: str = "Lima") -> Tuple[str, str]:
    """Construye mensaje para Libro de Reclamaciones INDECOPI."""
    subject = f"Libro de Reclamaciones INDECOPI - FiberPro - {sede}"
    body = (
        f"Su reclamo fue recibido correctamente.\n"
        f"Número de registro: {ticket_name}\n\n"
        f"Adjunto encontrará su constancia."
    )
    return subject, body

def build_maxpro_email(ticket_name: str) -> Tuple[str, str]:
    """Construye mensaje para MAXPRO (Chincha-Pisco)."""
    subject = "Confirmación de Libro de Reclamaciones - MAXPRO"
    body = f"Su reclamo fue registrado con el número: {ticket_name}."
    return subject, body