# app/core/odoo_client.py
import xmlrpc.client
from app.core.config import settings

class OdooClient:
    def __init__(self):
        # 1. Atributos del objeto (Estado inicial)
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self._uid = None
        self._common = None
        self._models = None

    @property
    def common(self):
        """Conexión perezosa (Lazy) al servicio common de Odoo"""
        if self._common is None:
            self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        return self._common

    @property
    def models(self):
        """Conexión perezosa al servicio object (modelos) de Odoo"""
        if self._models is None:
            self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return self._models

    def authenticate(self) -> int:
        """Autentica contra Odoo y guarda el uid en memoria"""
        if self._uid is None:
            self._uid = self.common.authenticate(
                self.db, 
                self.username, 
                self.password, 
                {}
            )
            if not self._uid:
                raise ValueError("Fallo de autenticación en Odoo: Revisa tus credenciales en el .env")
        return self._uid

    def execute_kw(self, model: str, method: str, args: list = None, kwargs: dict = None):
        """Ejecuta cualquier método ORM de Odoo (search, read, create, write, etc.)"""
        uid = self.authenticate()
        return self.models.execute_kw(
            self.db,
            uid,
            self.password,
            model,
            method,
            args or [],
            kwargs or {}
        )

# Creamos una instancia global lista para inyectar en las rutas
odoo_client = OdooClient()