import smtplib
import os
import xmlrpc.client
import logging
import base64
from app.core.odoo_client import detect_name_type_from_base64
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
    SENDGRID_API_KEY_MP: str = ""
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
    from_email_maxpro: Optional[str] = None,
    api_key_override: Optional[str] = None,
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
        from_email_maxpro=from_email_maxpro,
        api_key_override=api_key_override,
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

def send_maxpro_legal_email(ticket_name: str, data: dict, pdf_path: str) -> bool:
    """
    Procesa adjuntos y envía el correo de MaxPro al usuario y al administrador.
    Usa MAIL_USERNAME_MP exclusivamente.
    """
    user_email = str(data.get("correoelectronico", "") or "").strip()
    mail_username_mp = str(getattr(settings, "MAIL_USERNAME_MP", "") or "").strip()
    sendgrid_api_key_mp = str(getattr(settings, "SENDGRID_API_KEY_MP", "") or "").strip()
    
    subject = f"Libro de Reclamaciones INDECOPI - MAXPRO - {ticket_name}"
    body = (
        f"Estimado(a) {data.get('nombrescompletos', '')} {data.get('apellidoscompletos', '')},\n\n"
        f"Tu reclamo fue recibido correctamente. Número: {ticket_name}.\n\n"
        f"Adjunto encontrarás la constancia de tu reclamo.\n\n"
        f"Saludos,\n"
        f"MAXPRO"
    )
    
    if not sendgrid_api_key_mp:
        logger.error("SENDGRID_API_KEY_MP no configurada — no se pueden enviar correos de MaxPro")
        return False
    
    # Procesar adjuntos del frontend
    attachments = []
    if data.get("pruebas"):
        raw = data["pruebas"].split(",", 1)[-1] if "," in data["pruebas"] else data["pruebas"]
        try:
            name, mime = detect_name_type_from_base64(raw)
            attachments.append((name, mime, base64.b64decode(raw)))
        except Exception as e:
            logger.warning("Error procesando archivo para correo MaxPro: %s", e)
            
    success = True
    
    # 1. Enviar al usuario si autorizó correo
    if user_email:
        if not _send_legal_email(
            recipient=user_email,
            subject=subject,
            body=body,
            pdf_path=pdf_path,
            attachments=attachments if attachments else None,
            cc_receptor=False,
            from_email_maxpro=mail_username_mp,
            api_key_override=sendgrid_api_key_mp,
        ):
            success = False
        logger.info("Correo MaxPro enviado al usuario: %s", user_email)
    else:
        logger.warning("Usuario MaxPro sin correo electrónico")
            
    # 2. Enviar copia a MAIL_USERNAME_MP (exclusivo de MaxPro)
    if mail_username_mp:
        if not _send_legal_email(
            recipient=mail_username_mp,
            subject=f"[COPIA ADMIN MAXPRO] {subject}",
            body=f"Ticket: {ticket_name}\nUsuario: {user_email}\n\n{body}",
            pdf_path=pdf_path,
            attachments=attachments if attachments else None,
            cc_receptor=False,
            from_email_maxpro=mail_username_mp,
            api_key_override=sendgrid_api_key_mp,
        ):
            success = False
        logger.info("Copia de correo MaxPro enviada a: %s", mail_username_mp)
    else:
        logger.warning("MAIL_USERNAME_MP no configurado en .env")
        
    return success