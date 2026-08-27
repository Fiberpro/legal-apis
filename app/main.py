import base64
import logging
import mimetypes
import os
from email.message import EmailMessage
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.core.odoo_client import (attach_bytes, detect_name_type_from_base64, odoo, odoo_2,
                                  resolve_many2one_value, send_smtp_email, settings, validate_date, clean_base64)
from app.pdf_utils import generar_pdf, generar_pdf_osiptel

app = FastAPI(title="API Legal - FiberPro", version="2.1.0")
logger = logging.getLogger("api_legal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

DATE_FIELDS = {"fechaEmisionDocumentoIdentidad", "fechaNacimiento", "fechaVencimiento", "fechaEmisionFC", "fechaVencimientoFC", "fechaEstimadaPagoFC", "fechaInicioCalidadI", "fechaIncumplimientos", "fechAproximadaIncumplimiento", "fechaCualPincumplimiento", "fechaEmisionIncumplimineto", "fechavencimientoIncumplimineto", "fechaAproxInfoOmitida", "fechaInicioProblemafs", "fechaReactivarServicio", "fechaPagoPendiente", "fechaSIMCARD", "fechaContratacionServicioInstalacion", "fechaSolicitudTrasladoInstalacion", "fechaContratacionSInstalacion", "fechaSolicitudBaja", "fechaSolicitudSuspensionBaja", "fechaEmisionBaja", "fechaVencimientoBaja", "fechaEmisionContratacion", "fechaVencimientoContratacion", "fechaSolicitudMigracionX", "fechaEmisionMigracionIII", "fechaMovimientoMigracion", "fechaEmisionII", "fechaVencimientoMigracionII", "fechaEmisionMigracion", "fechaVencimientoMigracion", "fechaSolicitudX", "fechaEmisionX", "fechaVencimientoX", "fechaSolicitudFacturacionX"}
ALIASES = {"tipoUsuario": "tipo_de_usuario", "numeroDocumentIdentidad": "numero_documento_identidad_reclamo", "tipoDocumentoIdentidad": "tipo_documento_identidad", "nombre": "nombre_cliente", "numeroContacto": "nro_contacto", "numDoc": "nro_documento", "distritos": "distrito_cliente", "direccion": "direccion_cliente", "correo": "correo_electronico", "booleanValue": "notificacion_por_correo_electronico", "idReclamo": "materia_reclamable", "idReclamoEscogido": "problema_espec", "empresaOperadora": "empresa_operadora_dsr", "servicioContratado": "servicio_contratado_dsr", "numeroServicioContratado": "nmero_cdigo_servicio_contrato_dsr", "servicioMateriaReclamo": "servicio_materia_de_reclamo", "cartaPoder": "carta_de_poder", "hojaDocumentoAdjuntada": "adjunta_doc_cobro", "adjuntarVinculo": "documento", "vinculoAdjuntarSolicitud": "documento_1", "vinculoSolicitudReclamo": "vinculo_de_documento_adjuntado", "adjuntarSolicitudReclamoCuatro": "vinculo_del_documento_adjuntando", "solicitudBajaReclamo": "vinculo_del_documento_2", "adjuntarVinculoSolicitud": "vinculo_del_documento_1"}

def require(data, fields):
    missing = next((field for field in fields if field not in data), None)
    if missing:
        raise HTTPException(400, f"Falta el campo requerido: {missing}")

def create_ticket(client, model, data, extra=None):
    fields = client.execute_kw(model, "fields_get", [], {"attributes": ["type"]})
    payload = {key: value for key, value in data.items() if key in fields and value is not None}
    payload.update({target: data[source] for source, target in ALIASES.items()
                    if target in fields and data.get(source) is not None})
    payload.update({key: value for key, value in (extra or {}).items() if key in fields and value is not None})
    
    # Extraemos y limpiamos el base64
    pruebas_b64 = data.get("pruebas") or (extra or {}).get("pruebas")
    if isinstance(pruebas_b64, str) and "," in pruebas_b64:
        pruebas_b64 = pruebas_b64.split(",", 1)[-1]
    
    # Quitamos del payload para evitar problemas durante el create
    payload.pop("pruebas", None)
    
    # 1. Creamos el ticket SIN el archivo
    ticket_id = client.execute_kw(model, "create", [payload])
    
    # 2. Adjuntamos el archivo bypassando external_attachment_storage
    if pruebas_b64 and ticket_id:
        try:
            # Detectar nombre y mimetype
            name, mime = detect_name_type_from_base64(pruebas_b64)
            
            # --- PASO A: Eliminar attachments previos de este campo (si existen) ---
            existing = client.execute_kw("ir.attachment", "search", [
                [("res_model", "=", model), ("res_id", "=", ticket_id), ("res_field", "=", "pruebas")]
            ])
            if existing:
                client.execute_kw("ir.attachment", "unlink", [existing])
            
            # --- PASO B: Crear attachment HUÉRFANO (sin res_model/res_id) ---
            # El módulo external_attachment_storage ignora attachments sin res_id
            attachment_id = client.execute_kw("ir.attachment", "create", [{
                "name": name,
                "type": "binary",
                "datas": pruebas_b64,
                "mimetype": mime,
            }])
            
            # --- PASO C: Vincular al registro con skip_external_sync=True ---
            # El write del módulo SÍ respeta este contexto y NO sube a external
            client.execute_kw(
                "ir.attachment",
                "write",
                [[attachment_id], {
                    "res_model": model,
                    "res_id": ticket_id,
                    "res_field": "pruebas",
                }],
                {"context": {"skip_external_sync": True}}
            )
            
            # Verificación
            check = client.execute_kw(model, "read", [[ticket_id]], {"fields": ["pruebas"]})[0]
            has_file = bool(check.get("pruebas"))
            print(f"pruebas guardado: {has_file}", flush=True)
            logger.info(f"✅ Archivo adjuntado al ticket {ticket_id}: {has_file}")
            
        except Exception as e:
            print(f"ERROR write pruebas: {e}", flush=True)
            logger.error(f"❌ Error al adjuntar archivo en Odoo: {e}", exc_info=True)
            raise HTTPException(500, f"Error guardando archivo: {e}")

    return ticket_id, client.execute_kw(model, "read", [[ticket_id]], {"fields": ["name"]})[0].get("name", str(ticket_id))

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
        username, password = username or settings.MAIL_USERNAME, password if password is not None else settings.MAIL_PASSWORD
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

def legal_ticket(data, model):
    for field in DATE_FIELDS.intersection(data): data[field] = validate_date(data[field])
    require(data, ["tipoUsuario", "numeroDocumentIdentidad", "nombre", "apellidos", "correo"])
    try:
        ticket_id, ticket_name = create_ticket(odoo, model, data, {"state": "draft", "medio_reclamo": "WEB", "medio_queja": "WEB"})
        return {"success": True, "ticket_id": ticket_id, "ticket_name": ticket_name}
    except Exception as exc:
        raise HTTPException(400, f"Error creating ticket: {exc}") from exc

@app.post("/api/reclamos/reclamo")
def crear_reclamo(data: dict = Body(...)): return legal_ticket(data, "reclamosfp")

@app.post("/api/reclamos/queja")
def crear_queja(data: dict = Body(...)): return legal_ticket(data, "quejasfp")

@app.post("/api/reclamos/apelaciones")
def crear_apelacion(data: dict = Body(...)): return legal_ticket(data, "apelacionfp")

def libro_data(data):
    require(data, ["tipo", "tipodocumento", "numerodocumento", "nombrescompletos", "apellidoscompletos", "correoelectronico", "materiareclamable", "productos", "precio", "detalle", "pedido"])
    
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
        "pruebas": pruebas_b64
    }

@app.post("/api/libroreclamaciones")
def crear_libro(data: dict = Body(...)):
    try:
        ticket_id, ticket_name = create_ticket(odoo, "indecopi.complaints", {}, libro_data(data))
        return {"ticket_id": ticket_name, "message": "Libro de reclamacion registrado correctamente."}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.post("/api/libroreclamaciones/v2")
def crear_libro_v2(data: dict = Body(...)):
    if str(data.get("sedesicalima", "")).strip() != "1": raise HTTPException(400, "Solo se registran reclamos de Lima en Odoo.")
    pdf_path = None
    try:
        ticket_id, ticket_name = create_ticket(odoo, "indecopi.complaints", {}, libro_data(data))
        data["ticket_number"] = ticket_name
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, f"Error registrando en Odoo: {exc}") from exc
    try:
        pdf_path = generar_pdf(data)
    except Exception as exc: raise HTTPException(500, f"Error generando PDF: {exc}") from exc
    try:
        attachment = None
        if data.get("pruebas"):
            raw = data["pruebas"].split(",", 1)[-1]
            name, mime = detect_name_type_from_base64(raw)
            attachment = (name, mime, base64.b64decode(raw))
            
        send_pdf(
            data["correoelectronico"],
            "Libro de Reclamaciones INDECOPI - FiberPro - Lima",
            f"Tu reclamo fue recibido correctamente. Número: {ticket_name}.",
            pdf_path,
            attachment=attachment
        )
    except Exception as exc:
        raise HTTPException(500, f"Error enviando correo SMTP: {exc}") from exc
    finally:
        if pdf_path and os.path.exists(pdf_path): os.unlink(pdf_path)
    return {"success": True, "ticket_id": ticket_name, "message": "Reclamo registrado y constancia enviada."}

@app.post("/api/libroreclamaciones/chincha-pisco")
def crear_libro_maxpro(data: dict = Body(...)):
    pdf_path = None
    try:
        payload = libro_data(data)
        for field in ("departamento", "provincias", "distrito", "materia_reclamo"):
            payload[field] = resolve_many2one_value(odoo_2, "indecopi.complaints", field, payload.get(field))
        _, ticket_name = create_ticket(odoo_2, "indecopi.complaints", {}, payload)
        
        data["ticket_number"], pdf_path = ticket_name, generar_pdf(data)
        attachment = None
        if data.get("pruebas"):
            raw = data["pruebas"].split(",", 1)[-1]
            name, mime = detect_name_type_from_base64(raw)
            attachment = (data.get("pruebasNombre", name), data.get("pruebasTipo", mime), base64.b64decode(raw))
        send_pdf(data["correoelectronico"], "Confirmacion de Libro de Reclamaciones - MAXPRO", f"Tu reclamo fue registrado con el numero: {ticket_name}.", pdf_path, attachment, settings.MAIL_USERNAME_MP, settings.MAIL_PASSWORD_MP)
        return {"success": True, "ticket_id": ticket_name, "message": "Libro de reclamacion registrado correctamente."}
    except HTTPException: raise
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    except Exception as exc: raise HTTPException(500, str(exc)) from exc
    finally:
        if pdf_path and os.path.exists(pdf_path): os.unlink(pdf_path)

@app.post("/api/enviar_pdf")
def enviar_pdf(data: dict = Body(...)):
    return enviar_constancia(data, False)

def enviar_constancia(data, osiptel=False):
    pdf_path = None
    try:
        pdf_path = generar_pdf_osiptel(data) if osiptel else generar_pdf(data)
        recipient = settings.MAIL_RECEPTOR
        source = data.get("datos_generales", data)
        subject = "Formulario OSIPTEL - Reclamo / Queja - Sede ICA" if osiptel else "Libro de Reclamaciones INDECOPI - FiberPro-ICA"
        body = f"Cliente: {source.get('nombrescompletos', '')} {source.get('apellidoscompletos', '')}\nDocumento: {source.get('numerodocumento', '')}"
        
        attachment = None
        if source.get("pruebas"):
            raw = source["pruebas"].split(",", 1)[-1]
            name, mime = detect_name_type_from_base64(raw)
            attachment = (name, mime, base64.b64decode(raw))
            
        send_pdf(recipient, subject, body, pdf_path, attachment)
        return {"success": True, "message": f"PDF enviado correctamente a {recipient}"}
    except Exception as exc: raise HTTPException(500, str(exc)) from exc
    finally:
        if pdf_path and os.path.exists(pdf_path): os.unlink(pdf_path)

@app.post("/api/osiptel/ica")
def osiptel_ica(data: dict = Body(...)): return enviar_constancia(data, True)

@app.post("/api/osiptel/ica/v2")
def osiptel_ica_v2(data: dict = Body(...)):
    if not data.get("datos_generales"): raise HTTPException(400, "Estructura inválida: datos_generales no encontrado")
    return enviar_constancia(data, True)