import base64
import logging
from email.message import EmailMessage
from typing import List, Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, From, To, Content, Attachment,
    FileContent, FileName, FileType, Disposition, MimeType
)

from app.core.config import settings
logger = logging.getLogger("email_service")

def _safe(value) -> str:
    """Devuelve `value` como string sin espacios, o '' si es None."""
    return (str(value) if value is not None else "").strip()

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
    from_email_maxpro: Optional[str] = None,
    api_key_override: Optional[str] = None,
) -> bool:
    
    override = _safe(api_key_override)
    if override:
        api_key = override
    else:
        api_key = _safe(getattr(settings, "SENDGRID_API_KEY", None))
    # Acceso defensivo: si alguien borra/renombra una variable, no rompemos.
    
    receptor = _safe(getattr(settings, "MAIL_USERNAME", None)) or _safe(
        getattr(settings, "MAIL_RECEPTOR", None)
    )
    
    if from_email_maxpro:
        from_addr = _safe(from_email_maxpro)
    else:
        from_addr = _safe(
            getattr(settings, "MAIL_USERNAME", None)
            or getattr(settings, "FROM_EMAIL", None)
        ) or "noreply@fiberpro.pe"
    
    # from_addr = _safe(
    #     getattr(settings, "MAIL_USERNAME", None)
    #     or getattr(settings, "FROM_EMAIL", None)
    # ) or "noreply@fiberpro.pe"
    
    if not api_key:
        logger.error("SENDGRID_API_KEY no configurada — abortando envío")
        return False

    # Construir destinatarios
    to_emails = []
    recipient_clean = _safe(recipient)
    if recipient_clean:
        to_emails.append(To(recipient_clean))

    if cc_receptor and receptor and receptor != recipient_clean:
        to_emails.append(To(receptor))

    if not to_emails:
        logger.warning("No hay destinatarios válidos")
        return False

    # Construir mensaje
    from_email = From(from_addr)
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
            logger.error("Error adjuntando PDF: %s", pdf_path,  e)

    # Adjuntar archivos del frontend
    if attachments:
        for name, mime, file_bytes in attachments:
            try:
                mail.add_attachment(_build_sendgrid_attachment(name, mime, file_bytes))
            except Exception as e:
                logger.warning("Error adjuntando %s: %s", name, e)

    # Enviar
    try:
        sg = SendGridAPIClient(api_key)
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