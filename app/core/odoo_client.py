import smtplib
import os
import io
import base64
import mimetypes
import xmlrpc.client
import socket
import smtplib
import xmlrpc.client
import re
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from PIL import Image
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Configuración de Variables de Entorno ---
class Settings(BaseSettings):
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USER: str
    ODOO_PASSWORD: str

    ODOO_URL_2: str
    ODOO_DB_2: str
    ODOO_USER_2: str
    ODOO_PASSWORD_2: str

    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_USERNAME: str
    MAIL_PASSWORD: str = ""
    MAIL_USERNAME_MP: str = ""
    MAIL_PASSWORD_MP: str = ""
    MAIL_RECEPTOR: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# --- Clase Cliente Odoo ---
class OdooClient:
    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url
        self.db = db
        self.username = user
        self.password = password
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

    def authenticate(self) -> int:
        if not self._uid:
            self._uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not self._uid:
                raise ValueError(f"Fallo de autenticación Odoo en {self.url}")
        return self._uid

    def execute_kw(self, model: str, method: str, args: list = None, kwargs: dict = None):
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
odoo_2 = OdooClient(
    url=settings.ODOO_URL_2,
    db=settings.ODOO_DB_2,
    user=settings.ODOO_USER_2,
    password=settings.ODOO_PASSWORD_2
)

# --- Funciones de Utilidad ---
def clean_base64(b64_string):
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

def attach_file_to_ticket(client, model, ticket_id, b64_string, filename="documento_adjunto"):
    if not b64_string:
        return False
    if isinstance(b64_string, str) and "," in b64_string:
        b64_string = b64_string.split(",", 1)[-1]
    
    try:
        raw_bytes = base64.b64decode(b64_string)
        binary_data = xmlrpc.client.Binary(raw_bytes)
    except Exception:
        return False

    # Crear ir.attachment vinculado al registro
    attachment_id = client.execute_kw("ir.attachment", "create", [{
        "name": filename,
        "type": "binary",
        "datas": binary_data,
        "res_model": model,
        "res_id": ticket_id,
        "mimetype": detect_name_type_from_base64(b64_string)[1],
    }])
    
    # Opcional: actualizar el campo binario con el mismo valor
    client.execute_kw(model, "write", [[ticket_id], {"pruebas": binary_data}])
    
    return attachment_id

def to_odoo_binary(b64_string: str):
    """
    Convierte un string Base64 (puro o con data:...) en xmlrpc.client.Binary.
    Odoo 17 requiere este formato para campos Binary vía XML-RPC.
    """
    if not b64_string:
        return False
    if isinstance(b64_string, str) and "," in b64_string:
        b64_string = b64_string.split(",", 1)[-1]
    try:
        raw_bytes = base64.b64decode(b64_string)
        return xmlrpc.client.Binary(raw_bytes)
    except Exception:
        return False

def validate_date(date_str):
    if not date_str:
        return False
    try:
        date_obj = datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return False

def detect_name_type_from_base64(b64str, default_name='documento_adjunto'):
    try:
        raw = base64.b64decode(b64str)
    except Exception:
        return f"{default_name}.bin", 'application/octet-stream'
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img_format = img.format.lower()
            mime = f'image/{img_format}'
            ext = mimetypes.guess_extension(mime) or f'.{img_format}'
            return f"{default_name}{ext}", mime
    except Exception:
        pass
    if raw.startswith(b"%PDF"):
        return f"{default_name}.pdf", 'application/pdf'
    return f"{default_name}.bin", 'application/octet-stream'

def resolve_many2one_value(odoo_instance: OdooClient, model_name: str, field_name: str, raw_value):
    if raw_value in (None, '', False):
        return False

    raw_value_str = str(raw_value).strip()
    fields_info = odoo_instance.execute_kw(
        model_name, 'fields_get',
        [[field_name]],
        {'attributes': ['type', 'relation']}
    )

    field_info = fields_info.get(field_name, {})
    relation_model = field_info.get('relation')
    if field_info.get('type') != 'many2one' or not relation_model:
        return raw_value

    if isinstance(raw_value, int) or raw_value_str.isdigit():
        record_id = int(raw_value)
        exists = odoo_instance.execute_kw(
            relation_model, 'search_count',
            [[['id', '=', record_id]]]
        )
        if not exists:
            raise ValueError(f"El ID {record_id} no existe en Odoo para el campo {field_name}.")
        return record_id

    matches = odoo_instance.execute_kw(
        relation_model, 'name_search',
        [raw_value_str],
        {'operator': 'ilike', 'limit': 1}
    )
    if not matches:
        raise ValueError(f"No se encontró '{raw_value_str}' para el campo {field_name}. Envía el ID de Odoo.")

    return matches[0][0]

def attach_bytes(email_message: EmailMessage, filename: str, content_type: str, file_bytes: bytes):
    maintype, subtype = "application", "octet-stream"
    if content_type and "/" in content_type:
        maintype, subtype = content_type.split("/", 1)
    email_message.add_attachment(
        file_bytes,
        maintype=maintype,
        subtype=subtype,
        filename=filename
    )

def send_smtp_email(email_message: EmailMessage, recipients: list, username: str, password: str, sender_name: str = ""):
    if not username or not password:
        raise ValueError("Credenciales SMTP no configuradas.")

    if sender_name:
        email_message["From"] = formataddr((sender_name, username))
    elif not email_message.get("From"):
        email_message["From"] = username

    if not email_message.get("To"):
        email_message["To"] = ", ".join(recipients)
    
    host = settings.MAIL_SERVER
    port = settings.MAIL_PORT
    
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_INET,
                                   socket.SOCK_STREAM)
        if not infos:
            raise OSError(f"No se pudo resolver {host}:{port} por IPv4")
        host_to_connect = infos[0][4][0]
    except socket.gaierror:
        host_to_connect = host

    smtp_class = smtplib.SMTP_SSL if settings.MAIL_USE_SSL else smtplib.SMTP
    with smtp_class(host_to_connect, port, timeout=30) as smtp:
        if settings.MAIL_USE_TLS and not settings.MAIL_USE_SSL:
            smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(email_message, from_addr=username, to_addrs=recipients)
