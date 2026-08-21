# app/core/email_service.py
import base64
import logging
from email.message import EmailMessage
from typing import List, Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, From, To, Content, Attachment,
    FileContent, FileName, FileType, Disposition, MimeType
)

from app.core.config import settings
logger = logging.getLogger("email_service")

def _build_sendgrid_attachment(filename: str, content_type: str, file_bytes: bytes) -> Attachment:
    """Construye un attachment de SendGrid desde bytes."""
    att = Attachment()
    att.file_content = base64.b64encode(file_bytes).decode("ascii")
    att.file_name = filename
    att.file_type = content_type or "application/octet-stream"
    att.disposition = "attachment"
    return att

def send_legal_email(
    recipient: str,
    subject: str,
    body: str,
    pdf_path: Optional[str] = None,
    attachments: Optional[List[Tuple[str, str, bytes]]] = None,
    cc_receptor: bool = True,
) -> bool:
    """
    Envía correo vía SendGrid (obligatorio en Digital Ocean).
    
    Args:
        recipient: Correo del usuario (puede estar vacío si no autorizó)
        subject: Asunto
        body: Cuerpo en texto plano
        pdf_path: Ruta al PDF de constancia
        attachments: Lista de (nombre, mime_type, bytes) de archivos del frontend
        cc_receptor: Si True, envía copia a MAIL_RECEPTOR
    
    Returns:
        True si se envió, False si no hay destinatarios o falló SendGrid
    """
    if not settings.SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY no configurada")
        return False

    # Construir destinatarios
    to_emails = []
    recipient = (recipient or "").strip()
    if recipient:
        to_emails.append(To(recipient))

    if cc_receptor:
        receptor = (settings.MAIL_RECEPTOR or "").strip()
        if receptor and receptor != recipient:
            to_emails.append(To(receptor))  # CC vía To adicional

    if not to_emails:
        logger.warning("No hay destinatarios válidos")
        return False

    # Construir mensaje
    from_email = From(settings.MAIL_USERNAME or settings.FROM_EMAIL or "noreply@fiberpro.pe")
    mail = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
    )
    mail.add_content(Content(MimeType.text, body))

    # Adjuntar PDF
    if pdf_path:
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            mail.add_attachment(_build_sendgrid_attachment(
                "Constancia_Legal.pdf", "application/pdf", pdf_bytes
            ))
        except Exception as e:
            logger.error("Error adjuntando PDF: %s", e)

    # Adjuntar archivos del frontend
    if attachments:
        for name, mime, file_bytes in attachments:
            try:
                mail.add_attachment(_build_sendgrid_attachment(name, mime, file_bytes))
            except Exception as e:
                logger.warning("Error adjuntando %s: %s", name, e)

    # Enviar
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(mail)
        status = getattr(response, "status_code", 0)
        if 200 <= status < 300:
            logger.info("Email enviado vía SendGrid a %s (status=%s)", [t.email for t in to_emails], status)
            return True
        else:
            logger.error("SendGrid status=%s", status)
            return False
    except Exception as e:
        logger.exception("Error enviando email vía SendGrid: %s", e)
        return False