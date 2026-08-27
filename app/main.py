import base64
import logging
import os
from typing import Optional
from email.message import EmailMessage
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.core.odoo_client import (clean_base64, attach_bytes, detect_name_type_from_base64, odoo, odoo_2,
                                  resolve_many2one_value, send_smtp_email, settings as odoo_settings, validate_date)
from app.core.email_service import send_legal_email
from app.mappings import (
    build_odoo_payload,
    normalize_for_pdf,
    extract_email_attachments,
    DATE_FIELDS,
    REQUIRED_FIELDS,
)
from app.pdf_utils_osiptel_v2 import generar_pdf as generar_pdf_osiptel_v2
from app.pdf_utils import generar_pdf, generar_pdf_osiptel

app = FastAPI(title="API Legal - FiberPro", version="2.1.0")
logger = logging.getLogger("api_legal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

def require(data, fields):
    """Valida que los campos requeridos existan en el payload y no estén vacíos."""
    for field in fields:
        val = data.get(field)
        if val is None or val == "":
            raise HTTPException(400, f"Falta el campo requerido o está vacío: {field}")

def create_ticket_with_mapping(client, model: str, data: dict):
    try:
        fields_info = client.execute_kw(model, "fields_get", [], {"attributes": ["type"]})
        odoo_fields = set(fields_info.keys())
    except Exception as exc:
        logger.error("No se pudo obtener fields_get de %s: %s", model, exc)
        raise HTTPException(500, f"Error consultando modelo Odoo {model}") from exc

    # Construir payload con mapeo completo
    payload, unknown = build_odoo_payload(data, model, odoo_fields)
    if unknown:
        logger.info("Campos ignorados (no mapeados o no existen en Odoo): %s", unknown)

    # Limpiar base64 de campos binarios dinámicamente
    # Obtenemos los campos tipo binary directamente de Odoo
    binary_odoo_keys = {k for k, v in fields_info.items() if v.get("type") == "binary"}
    
    for key in list(payload.keys()):
        if key in binary_odoo_keys and isinstance(payload[key], str):
            cleaned = clean_base64(payload[key])
            if cleaned and len(cleaned) > 100:
                payload[key] = cleaned
            else:
                payload.pop(key, None)

    # Crear ticket
    try:
        ticket_id = client.execute_kw(model, "create", [payload])
    except Exception as exc:
        logger.error("Error creando ticket en Odoo (%s): %s", model, exc)
        raise HTTPException(400, f"Error creating ticket: {exc}") from exc

    # Leer nombre
    try:
        result = client.execute_kw(model, "read", [[ticket_id]], {"fields": ["name"]})
        ticket_name = result[0].get("name", str(ticket_id)) if result else str(ticket_id)
    except Exception as exc:
        logger.warning("No se pudo leer nombre del ticket %s: %s", ticket_id, exc)
        ticket_name = str(ticket_id)

    return ticket_id, ticket_name

@app.get("/api/distritos")
@app.get("/api/ubicaciones/distritos")
def listar_distritos(
    provincia_id: str | None = Query(default=None),
    provincia: str | None = Query(default=None),
):
    """Devuelve los distritos de Odoo para una provincia, por ID o nombre."""
    value = (provincia_id if isinstance(provincia_id, str) else provincia or "").strip()
    if not value:
        raise HTTPException(400, "Envía provincia_id o provincia.")
    try:
        if value.isdigit():
            city_id = int(value)
        else:
            cities = odoo.execute_kw("res.city", "name_search", [value], {"operator": "=ilike", "limit": 2})
            if not cities:
                raise HTTPException(404, f"No se encontró la provincia: {value}")
            city_id = cities[0][0]
        districts = odoo.execute_kw(
            "l10n_pe.res.city.district", "search_read",
            [[("city_id", "=", city_id)]],
            {"fields": ["id", "name", "code"], "order": "name"},
        )
        return [
            {
                "id": row["id"], "id_distrito": row["id"], "value": row["id"],
                "name": row["name"], "nombre": row["name"], "distrito": row["name"],
                "nombre_distrito": row["name"], "label": row["name"], "codigo": row.get("code"),
            }
            for row in districts
        ]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"No fue posible consultar distritos en Odoo: {exc}") from exc

@app.get("/api/distritos/{provincia_id}")
@app.get("/api/ubicaciones/distritos/{provincia_id}")
@app.get("/api/get_district/{provincia_id}")
def listar_distritos_por_provincia(provincia_id: str):
    return listar_distritos(provincia_id=provincia_id)

def send_pdf(recipient, subject, body, pdf_path, attachment=None, username=None, password=None):
    try:
        # Corrección: usar odoo_settings en lugar de settings
        username, password = username or odoo_settings.MAIL_USERNAME, password if password is not None else odoo_settings.MAIL_PASSWORD
        message = EmailMessage()
        message["Subject"], message["From"], message["To"] = subject, username, recipient
        message.set_content(body)
        with open(pdf_path, "rb") as pdf_file:
            attach_bytes(message, "Libro_de_Reclamaciones.pdf", "application/pdf", pdf_file.read())
        if attachment:
            attach_bytes(message, *attachment)
        send_smtp_email(message, [recipient], username, password)
    except Exception:
        logger.exception("No se pudo enviar el correo SMTP")
        raise

def process_legal_ticket(data: dict, model: str, tipo_label: str):
    pdf_path: Optional[str] = None
    
    try:
        # ─── 1. VALIDAR FECHAS ───
        for field in DATE_FIELDS.get(model, []):
            if field in data and data[field]:
                validated = validate_date(data[field])
                if validated is False and data[field] not in ("", None):
                    raise HTTPException(400, f"Fecha inválida en {field}: {data[field]}")
                data[field] = validated

        # ─── 3. CREAR TICKET EN ODOO ───
        ticket_id, ticket_name = create_ticket_with_mapping(odoo, model, data)
        logger.info("Ticket %s creado: %s (id=%s)", tipo_label, ticket_name, ticket_id)

        # ─── 4. GENERAR PDF ───
        pdf_sent = False
        email_sent = False
        error_pdf = None
        error_email = None

        try:
            pdf_data = normalize_for_pdf(data, model, ticket_name)
            pdf_path = generar_pdf_osiptel_v2(pdf_data)
            pdf_sent = True
            logger.info("PDF generado: %s", pdf_path)
        except Exception as exc:
            error_pdf = str(exc)
            logger.exception("Error generando PDF para %s %s", tipo_label, ticket_name)
        
        #─── 5. ENVIAR CORREO (SendGrid) ───
        if pdf_sent and pdf_path:
            try:
                recipient = (data.get("correo") or "").strip()
                
                # El frontend envía autorizacion o booleanValue (puede ser "True"/"False" string o bool)
                notify_val = data.get("autorizacion", data.get("booleanValue"))
                notify = str(notify_val).lower() in ("true", "1", "si", "yes")
                
                # Política de correo:
                # - Si autoriza, enviar al correo del usuario
                # - Enviar copia a MAIL_RECEPTOR siempre (para registro interno)
                # - No enviar si no hay ningún destinatario válido
                if not recipient and not odoo_settings.MAIL_RECEPTOR:
                    logger.info("No se envía correo: sin destinatario y sin MAIL_RECEPTOR")
                else:
                    subject = f"Constancia de {tipo_label} - FiberPro - {ticket_name}"
                    body = (
                        f"Estimado(a) {data.get('nombre', '')} {data.get('apellidos', '')},\n\n"
                        f"Su {tipo_label.lower()} ha sido registrado correctamente.\n"
                        f"Número de ticket: {ticket_name}\n\n"
                        f"Adjunto encontrará su constancia en PDF."
                    )
                    
                    attachments = extract_email_attachments(data, model)
                    
                    email_sent = send_legal_email(
                        recipient=recipient if notify else "",
                        subject=subject,
                        body=body,
                        pdf_path=pdf_path,
                        attachments=attachments,
                        cc_receptor=True,
                    )
                    
                    if not email_sent:
                        error_email = "Fallo en el envío vía SendGrid (ver logs)"
            except Exception as exc:
                error_email = str(exc)
                logger.exception("Error enviando correo para %s %s", tipo_label, ticket_name)

        # ─── 6. RESPUESTA JSON ───
        response = {
            "success": True,
            "ticket_id": ticket_id,
            "ticket_name": ticket_name,
            "pdf_sent": pdf_sent,
            "pdf_sent": False,
            "email_sent": email_sent,
        }
        
        if error_pdf:
            response["warning_pdf"] = "El ticket se creó pero no se pudo generar la constancia PDF."
        if error_email:
            response["warning_email"] = "El ticket y PDF se generaron pero no se pudo enviar el correo."

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error inesperado en process_legal_ticket: %s", exc)
        raise HTTPException(500, f"Error interno del servidor: {exc}") from exc
    finally:
        # ─── 7. LIMPIAR TEMPORALES ───
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
                logger.debug("Archivo temporal eliminado: %s", pdf_path)
            except Exception as e:
                logger.warning("No se pudo eliminar PDF temporal %s: %s", pdf_path, e)

@app.post("/api/reclamos/reclamo")
def crear_reclamo(data: dict = Body(...)): 
    return process_legal_ticket(data, "reclamosfp", "Reclamo")

@app.post("/api/reclamos/queja")
def crear_queja(data: dict = Body(...)): 
    return process_legal_ticket(data, "quejasfp", "Queja")

@app.post("/api/reclamos/apelaciones")
def crear_apelacion(data: dict = Body(...)): 
    return process_legal_ticket(data, "apelacionfp", "Apelación")

# =============================================================================
# ENDPOINTS LEGACY (INDECOPI) - No modificar
# =============================================================================

def libro_data(data):
    pruebas_b64 = data.get("pruebas")
    if pruebas_b64 and isinstance(pruebas_b64, str) and "," in pruebas_b64:
        pruebas_b64 = pruebas_b64.split(",", 1)[-1]

    return {
        "tipo": int(data["tipo"]) if data.get("tipo") else False, 
        "tipo_identificacion": data.get("tipodocumento"), 
        "nif": data.get("numerodocumento"), 
        "nombres": data.get("nombrescompletos"), 
        "apellidos": data.get("apellidoscompletos"), 
        "menor_edad": data.get("menorEdad"), 
        "departamento": data.get("departamento"), 
        "provincias": data.get("provincias"), 
        "distrito": data.get("distrito"), 
        "correo": data.get("correoelectronico"), 
        "movil": data.get("movil"), 
        "direccion": data.get("direccioncasa"), 
        "autorizacion": data.get("autorizacion"), 
        "nombreapoderado": data.get("nombrePadre"), 
        "materia_reclamo": data.get("materiareclamable"), 
        "especifique_reclamo": data.get("otrosreclamable"), 
        "identificion_producto_reclamo": data.get("productos"), 
        "monto_producto_reclamo": data.get("precio"), 
        "especifique_incoveniente": data.get("detalle"), 
        "pedido_concreto_consumidor": data.get("pedido"), 
        "pruebas": pruebas_b64,
    }

@app.post("/api/libroreclamaciones")
def crear_libro(data: dict = Body(...)):
    try:
        fields_info = odoo.execute_kw("indecopi.complaints", "fields_get", [], {"attributes": ["type"]})
        odoo_fields = set(fields_info.keys())
        payload, _ = build_odoo_payload(libro_data(data), "indecopi.complaints", odoo_fields)
        ticket_id = odoo.execute_kw("indecopi.complaints", "create", [payload])
        result = odoo.execute_kw("indecopi.complaints", "read", [[ticket_id]], {"fields": ["name"]})
        ticket_name = result[0].get("name", str(ticket_id)) if result else str(ticket_id)
        return {"ticket_id": ticket_name, "message": "Libro de reclamacion registrado correctamente."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@app.post("/api/libroreclamaciones/v2")
def crear_libro_v2(data: dict = Body(...)):
    if str(data.get("sedesicalima", "")).strip() != "1":
        raise HTTPException(400, "Solo se registran reclamos de Lima en Odoo.")
    pdf_path = None
    try:
        # Verificar si el archivo llegó
        if data.get("pruebas"):
            logger.info("Archivo recibido en request, longitud: %s", len(str(data["pruebas"])))
        else:
            logger.warning("No se recibió archivo en el request")
        #------------------------------------------------------------
        fields_info = odoo.execute_kw("indecopi.complaints", "fields_get", [], {"attributes": ["type"]})
        odoo_fields = set(fields_info.keys())
        # Verificar si 'pruebas' existe en Odoo
        if "pruebas" in odoo_fields:
            logger.info("Campo 'pruebas' existe en Odoo")
        else:
            logger.warning("Campo 'pruebas' NO existe en Odoo")
            # Buscar campos binary alternativos
            binary_fields = [k for k, v in fields_info.items() if v.get("type") == "binary"]
            logger.info("Campos binary disponibles: %s", binary_fields)
        #-----------------------------------------------------------------
        libro_payload = libro_data(data)
        payload, unknown = build_odoo_payload(libro_payload, "indecopi.complaints", odoo_fields)
        
        # Verificar que el archivo está en el payload
        if payload.get("pruebas"):
            logger.info("Archivo adjunto en payload para Odoo (tamaño: %s caracteres)", len(payload["pruebas"]))
        else:
            logger.warning("No se encontró 'pruebas' en el payload para Odoo")
        
        ticket_id = odoo.execute_kw("indecopi.complaints", "create", [payload])
        result = odoo.execute_kw("indecopi.complaints", "read", [[ticket_id]], {"fields": ["name"]})
        ticket_name = result[0].get("name", str(ticket_id)) if result else str(ticket_id)
        data["ticket_number"] = ticket_name
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error registrando en Odoo: %s", exc)
        raise HTTPException(500, f"Error registrando en Odoo: {exc}") from exc
    
    try:
        pdf_path = generar_pdf(data)
    except Exception as exc:
        raise HTTPException(500, f"Error generando PDF: {exc}") from exc
    
    try:
        # Preparar archivos adjuntos para el correo
        attachments = []
        if data.get("pruebas"):
            raw = data["pruebas"].split(",", 1)[-1] if "," in data["pruebas"] else data["pruebas"]
            try:
                name, mime = detect_name_type_from_base64(raw)
                attachments.append((name, mime, base64.b64decode(raw)))
                logger.info("Archivo preparado para correo: %s", name)
            except Exception as e:
                logger.warning("Error procesando archivo para correo: %s", e)
        
        # Obtener el correo del usuario y MAIL_USERNAME
        user_email = data.get("correoelectronico", "").strip()
        mail_username = getattr(odoo_settings, "MAIL_USERNAME", None)
        
        subject = f"Libro de Reclamaciones INDECOPI - FiberPro - {ticket_name}"
        body = (
            f"Estimado(a) {data.get('nombrescompletos', '')} {data.get('apellidoscompletos', '')},\n\n"
            f"Tu reclamo fue recibido correctamente. Número: {ticket_name}.\n\n"
            f"Adjunto encontrarás la constancia de tu reclamo.\n\n"
            f"Saludos,\n"
            f"FiberPro"
        )
        
        # Enviar al usuario si tiene correo
        if user_email:
            send_legal_email(
                recipient=user_email,
                subject=subject,
                body=body,
                pdf_path=pdf_path,
                attachments=attachments if attachments else None,
                cc_receptor=False,
            )
            logger.info("Correo enviado al usuario: %s", user_email)
        else:
            logger.warning("Usuario sin correo electrónico")
        
        # Enviar a MAIL_USERNAME (SIEMPRE)
        if mail_username:
            send_legal_email(
                recipient=mail_username,
                subject=f"[COPIA ADMIN] {subject}",
                body=f"Ticket: {ticket_name}\nUsuario: {user_email}\n\n{body}",
                pdf_path=pdf_path,
                attachments=attachments if attachments else None,
                cc_receptor=False,
            )
            logger.info("Correo enviado a MAIL_USERNAME: %s", mail_username)
        else:
            logger.warning("MAIL_USERNAME no configurado en .env")
            
    except Exception as exc:
        logger.exception("Error enviando correo: %s", exc)
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
    
    return {"success": True, "ticket_id": ticket_name, "message": "Reclamo registrado y constancia enviada."}

@app.post("/api/libroreclamaciones/chincha-pisco")
def crear_libro_maxpro(data: dict = Body(...)):
    pdf_path = None
    try:
        payload = libro_data(data)
        for field in ("departamento", "provincias", "distrito", "materia_reclamo"):
            payload[field] = resolve_many2one_value(odoo_2, "indecopi.complaints", field, payload.get(field))
        fields_info = odoo_2.execute_kw("indecopi.complaints", "fields_get", [], {"attributes": ["type"]})
        odoo_fields = set(fields_info.keys())
        p, _ = build_odoo_payload(payload, "indecopi.complaints", odoo_fields)
        ticket_id = odoo_2.execute_kw("indecopi.complaints", "create", [p])
        result = odoo_2.execute_kw("indecopi.complaints", "read", [[ticket_id]], {"fields": ["name"]})
        ticket_name = result[0].get("name", str(ticket_id)) if result else str(ticket_id)
        data["ticket_number"] = ticket_name
        pdf_path = generar_pdf(data)
        attachment = None
        if data.get("pruebas"):
            raw = data["pruebas"].split(",", 1)[-1]
            name, mime = detect_name_type_from_base64(raw)
            attachment = (data.get("pruebasNombre", name), data.get("pruebasTipo", mime), base64.b64decode(raw))
        send_legal_email(
            recipient=data["correoelectronico"],
            subject="Confirmacion de Libro de Reclamaciones - MAXPRO",
            body=f"Tu reclamo fue registrado con el numero: {ticket_name}.",
            pdf_path=pdf_path,
            attachments=[attachment] if attachment else None,
            cc_receptor=False,
        )
        return {"success": True, "ticket_id": ticket_name, "message": "Libro de reclamacion registrado correctamente."}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
            
@app.post("/api/enviar_pdf")
def enviar_pdf(data: dict = Body(...)):
    return enviar_constancia(data, False)

def enviar_constancia(data, osiptel=False):
    pdf_path = None
    try:
        pdf_path = generar_pdf_osiptel(data) if osiptel else generar_pdf(data)
        recipient = odoo_settings.MAIL_RECEPTOR
        source = data.get("datos_generales", data)
        subject = "Formulario OSIPTEL - Reclamo / Queja - Sede ICA" if osiptel else "Libro de Reclamaciones INDECOPI - FiberPro-ICA"
        body = f"Cliente: {source.get('nombrescompletos', '')} {source.get('apellidoscompletos', '')}\nDocumento: {source.get('numerodocumento', '')}"
        
        attachment = None
        if source.get("pruebas"):
            raw = source["pruebas"].split(",", 1)[-1]
            name, mime = detect_name_type_from_base64(raw)
            attachment = (name, mime, base64.b64decode(raw))
            
        send_legal_email(
            recipient=recipient,
            subject=subject,
            body=body,
            pdf_path=pdf_path,
            attachments=[attachment] if attachment else None,
            cc_receptor=False,
        )
        return {"success": True, "message": f"PDF enviado correctamente a {recipient}"}
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)

@app.post("/api/osiptel/ica")
def osiptel_ica(data: dict = Body(...)): 
    return enviar_constancia(data, True)

@app.post("/api/osiptel/ica/v2")
def osiptel_ica_v2(data: dict = Body(...)):
    if not data.get("datos_generales"): 
        raise HTTPException(400, "Estructura inválida: datos_generales no encontrado")
    return enviar_constancia(data, True)