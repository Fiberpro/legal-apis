import smtplib
import os
import io
import logging
import base64
import mimetypes
import xmlrpc.client
import socket
import smtplib
import re
from datetime import datetime
from email.message import EmailMessage
from typing import Optional, List
from email.utils import formataddr
from PIL import Image
from app.core.config import settings
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# --- Clase Cliente Odoo  ---
class OdooClient:
    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url
        self.db = db
        self.username = user
        self.password = password
        self._uid: Optional[int] = None
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
    def authenticate(self) -> int:
        if not self._uid:
            self._uid = self.common.authenticate(
                self.db, self.username, self.password, {}
            )
            if not self._uid:
                raise ValueError(f"Fallo de autenticación Odoo en {self.url}")
        return self._uid
    def execute_kw(
        self, model: str, method: str, args: list = None, kwargs: dict = None
    ):
        uid = self.authenticate()
        return self.models.execute_kw(
            self.db, uid, self.password, model, method, args or [], kwargs or {}
        )

# Instancia 1: FiberPro (Lima)
odoo = OdooClient(
    url=settings.ODOO_URL,
    db=settings.ODOO_DB,
    user=settings.ODOO_USER,
    password=settings.ODOO_PASSWORD
)

# Instancia 2: MaxPro (Chincha - Pisco)
if all([settings.ODOO_URL_2, settings.ODOO_DB_2, settings.ODOO_USER_2, settings.ODOO_PASSWORD_2]):
    odoo_2 = OdooClient(
        url=settings.ODOO_URL_2,
        db=settings.ODOO_DB_2,
        user=settings.ODOO_USER_2,
        password=settings.ODOO_PASSWORD_2,
    )
else:
    odoo_2 = None

# --- Funciones de Utilidad ---
def clean_base64(b64_string: Optional[str]) -> Optional[str]:
    """
    Limpia un string base64:
    - Remueve prefijo data:image/png;base64,...
    - Remueve saltos de línea, espacios, tabs
    - Devuelve string ASCII puro o None
    """
    if not b64_string:
        return None
    if isinstance(b64_string, str) and "," in b64_string:
        b64_string = b64_string.split(",", 1)[-1]
    # Eliminar cualquier whitespace (saltos de línea, espacios, tabs)
    b64_string = re.sub(r'[\s\n\r\t]', '', b64_string)
    return b64_string

def validate_date(date_str) -> Optional[str]:
    """
    Valida y normaliza una fecha a formato YYYY-MM-DD.
    Retorna False si es inválida (para compatibilidad con código existente).
    """
    if not date_str:
        return False
    try:
        date_obj = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return False

def detect_name_type_from_base64(b64str: str, default_name: str = "documento_adjunto") -> tuple:
    """Detecta MIME y extensión de un contenido base64 inspeccionando los bytes."""
    try:
        raw = __import__("base64").b64decode(b64str)
    except Exception:
        return f"{default_name}.bin", "application/octet-stream"
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img_format = img.format.lower() if img.format else "bin"
            mime = f"image/{img_format}"
            ext = mimetypes.guess_extension(mime) or f".{img_format}"
            return f"{default_name}{ext}", mime
    except Exception:
        pass
    if raw.startswith(b"%PDF"):
        return f"{default_name}.pdf", "application/pdf"
    return f"{default_name}.bin", "application/octet-stream"

def resolve_many2one_value(odoo_instance: OdooClient, model_name: str, field_name: str, raw_value):
    """
    Resuelve un valor many2one: si es string, hace name_search.
    Si es int, verifica que exista. Retorna el ID o False.
    
    Raises:
        ValueError: Si no encuentra el registro referenciado.
    """
    if raw_value in (None, "", False):
        return False

    raw_value_str = str(raw_value).strip()

    fields_info = odoo_instance.execute_kw(
        model_name, "fields_get",
        [[field_name]],
        {"attributes": ["type", "relation"]}
    )

    field_info = fields_info.get(field_name, {})
    relation_model = field_info.get("relation")

    if field_info.get("type") != "many2one" or not relation_model:
        return raw_value

    # Si ya es un ID numérico
    if isinstance(raw_value, int) or raw_value_str.isdigit():
        record_id = int(raw_value)
        exists = odoo_instance.execute_kw(
            relation_model, "search_count",
            [[["id", "=", record_id]]]
        )
        if not exists:
            raise ValueError(f"El ID {record_id} no existe en Odoo para el campo {field_name}.")
        return record_id

    # Buscar por nombre
    matches = odoo_instance.execute_kw(
        relation_model, "name_search",
        [raw_value_str],
        {"operator": "ilike", "limit": 1}
    )
    if not matches:
        raise ValueError(
            f"No se encontró '{raw_value_str}' para el campo {field_name}. "
            f"Envía el ID de Odoo."
        )

    return matches[0][0]

def attach_bytes(email_message: EmailMessage, filename: str, content_type: str, file_bytes: bytes):
    """
    Adjunta bytes a un EmailMessage.
    Nota: Para nuevo código, usar app.core.email_service.send_legal_email().
    """
    maintype, subtype = "application", "octet-stream"
    if content_type and "/" in content_type:
        maintype, subtype = content_type.split("/", 1)
    email_message.add_attachment(
        file_bytes,
        maintype=maintype,
        subtype=subtype,
        filename=filename
    )

def send_smtp_email(message: EmailMessage, recipients: List[str], username: str, password: str):
    """
    Envía un correo electrónico utilizando smtplib (fallback en caso de no usar SendGrid).
    """
    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            if settings.MAIL_USE_TLS:
                server.starttls()
            server.login(username, password)
            server.send_message(message, to_addrs=recipients)
    except Exception as e:
        logger.error(f"Error enviando correo SMTP: {e}")
        raise
    
# app/core/odoo_client.py (añadir al final del archivo)

def attach_file_bypass_external(
    client: OdooClient,
    model: str,
    record_id: int,
    field: str,
    base64_data: str,
) -> bool:
    """
    Adjunta un archivo a un registro de Odoo sin que external_attachment_storage
    lo suba a un storage externo.

    Args:
        client: Instancia de OdooClient
        model: Nombre del modelo (ej. 'indecopi.complaints')
        record_id: ID del registro
        field: Nombre del campo binary (ej. 'pruebas')
        base64_data: Contenido del archivo en base64 (sin prefijo)

    Returns:
        bool: True si se adjuntó correctamente, False en caso contrario.
    """
    if not base64_data or not record_id:
        logger.warning("No hay datos o ID válido para adjuntar")
        return False

    # Limpiar base64 (por si tiene prefijo)
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[-1]

    # Detectar nombre y mimetype
    name, mime = detect_name_type_from_base64(base64_data, default_name=field)

    try:
        # --- PASO A: Eliminar attachments previos de este campo ---
        existing = client.execute_kw(
            "ir.attachment",
            "search",
            [[("res_model", "=", model), ("res_id", "=", record_id), ("res_field", "=", field)]]
        )
        if existing:
            client.execute_kw("ir.attachment", "unlink", [existing])
            logger.info("Eliminados %s attachments previos para %s.%s", len(existing), model, field)

        # --- PASO B: Crear attachment HUÉRFANO (sin res_model/res_id) ---
        # El external_attachment_storage ignora attachments sin res_id
        attachment_id = client.execute_kw("ir.attachment", "create", [{
            "name": name,
            "type": "binary",
            "datas": base64_data,
            "mimetype": mime,
        }])
        logger.info("Attachment huérfano creado: id=%s, name=%s", attachment_id, name)

        # --- PASO C: Vincular al registro con skip_external_sync=True ---
        # El módulo respeta este contexto y NO sube a external
        client.execute_kw(
            "ir.attachment",
            "write",
            [[attachment_id], {
                "res_model": model,
                "res_id": record_id,
                "res_field": field,
            }],
            {"context": {"skip_external_sync": True}}
        )
        logger.info("Attachment vinculado a %s.%s (id=%s) con skip_external_sync", model, field, record_id)

        # Verificación opcional
        check = client.execute_kw(model, "read", [[record_id]], {"fields": [field]})[0]
        has_file = bool(check.get(field))
        logger.info("✅ Archivo guardado en Odoo: %s", has_file)
        return has_file

    except Exception as e:
        logger.error("❌ Error adjuntando archivo: %s", e, exc_info=True)
        return False