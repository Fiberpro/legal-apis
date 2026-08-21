# app/mappings.py
import base64
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("legal_mappings")

# =============================================================================
# MAPEO FRONTEND → ODOO (completo, por modelo)
# =============================================================================

RECLAMO_MAP = {
    "tipoUsuario": "tipo_de_usuario",
    "nombrePadre": "nombre_del_padre_abonado",
    "nombreMadre": "nombre_de_la_madre_abonado",
    "lugarNacimiento": "lugar_de_nacimiento_abonado",
    "fechaNacimiento": "fecha_de_nacimiento_abonado",
    "numeroDocumentIdentidad": "numero_documento_identidad_reclamo",
    "fechaEmisionDocumentoIdentidad": "fecha_emision_documento_identidad",
    "fechaVencimiento": "fecha_vencimiento_del_recibo_usuario",
    "montoTarifa": "monto_de_tarifa_usuario",
    "direccionFacturacion": "direccion_de_facturacion_usuario",
    "tipoDocumentoIdentidad": "tipo_documento_identidad",
    "nombre": "nombre_cliente",
    "apellidos": "apellidos",
    "relacion": "relacion_familiar",
    "razonSocial": "razon_social",
    "cartaPoder": "carta_de_poder",
    "numeroContacto": "nro_contacto",
    "tipoDoc": "tipo_doc",
    "numDoc": "nro_documento",
    "distritos": "distrito_cliente",
    "direccion": "direccion_cliente",
    "correo": "correo_electronico",
    "booleanValue": "notificacion_por_correo_electronico",
    "idReclamo": "materia_reclamable",
    "idReclamoEscogido": "problema_espec",
    "empresaOperadora": "empresa_operadora_dsr",
    "servicioContratado": "servicio_contratado_dsr",
    "numeroServicioContratado": "nmero_cdigo_servicio_contrato_dsr",
    "servicioMateriaReclamo": "servicio_materia_de_reclamo",
    # Campos específicos de materias
    "numeroReciboFC": "nmero_recibo_fc",
    "fechaEmisionFC": "fecha_emision_fc",
    "fechaVencimientoFC": "fecha_vencimiento_fc",
    "montoReciboFC": "monto_recibo_fc",
    "fechaEstimadaPagoFC": "fecha_estimada_pago_fc",
    "montoPagadoFC": "monto_pagado_fc",
    "montoReclamadoFC": "monto_reclamado_fc",
    "fechaInicioCalidadI": "fecha_inicio_calidad_i",
    "tipoProblemaCalidadI": "tipo_problema_calidad_i",
    "fechaIncumplimientos": "fecha_incumplimientos",
    "fechAproximadaIncumplimiento": "fech_aproximada_incumplimiento",
    "fechaCualPincumplimiento": "fecha_cual_pincumplimiento",
    "fechaEmisionIncumplimineto": "fecha_emision_incumplimineto",
    "fechavencimientoIncumplimineto": "fechavencimiento_incumplimineto",
    "montoReclamadoIncumplimiento": "monto_reclamado_incumplimiento",
    "fechaInicioProblemafs": "fecha_inicio_problemafs",
    "fechaReactivarServicio": "fecha_reactivar_servicio",
    "montoPagadoFaltaServicio": "monto_pagado_falta_servicio",
    "fechaContratacionServicioInstalacion": "fecha_contratacion_servicio_instalacion",
    "fechaSolicitudTrasladoInstalacion": "fecha_solicitud_traslado_instalacion",
    "fechaContratacionSInstalacion": "fecha_contratacion_s_instalacion",
    "fechaSolicitudBaja": "fecha_solicitud_baja",
    "fechaSolicitudSuspensionBaja": "fecha_solicitud_suspension_baja",
    "fechaEmisionBaja": "fecha_emision_baja",
    "fechaVencimientoBaja": "fecha_vencimiento_baja",
    "fechaEmisionContratacion": "fecha_emision_contratacion",
    "fechaVencimientoContratacion": "fecha_vencimiento_contratacion",
    "fechaSolicitudMigracionX": "fecha_solicitud_migracion_x",
    "fechaEmisionMigracionIII": "fecha_emision_migracion_iii",
    "fechaMovimientoMigracion": "fecha_movimiento_migracion",
    "fechaEmisionII": "fecha_emision_ii",
    "fechaVencimientoMigracionII": "fecha_vencimiento_migracion_ii",
    "fechaEmisionMigracion": "fecha_emision_migracion",
    "fechaVencimientoMigracion": "fecha_vencimiento_migracion",
    "fechaSolicitudX": "fecha_solicitud_x",
    "fechaEmisionX": "fecha_emision_x",
    "fechaVencimientoX": "fecha_vencimiento_x",
    "fechaSolicitudFacturacionX": "fecha_solicitud_facturacion_x",
    "descargoReclamo": "descargo_reclamo",
    "informacionNecesariaReclamo": "informacion_necesaria_reclamo",
    # Archivos
    "adjuntarVinculoSolicitud": "vinculo_del_documento_adjuntando",
    "adjuntarVinculo": "documento",
    "vinculoAdjuntarSolicitud": "documento_1",
    "vinculoSolicitudReclamo": "vinculo_de_documento_adjuntado",
    "adjuntarSolicitudReclamoCuatro": "vinculo_del_documento_adjuntando",
    "solicitudBajaReclamo": "vinculo_del_documento_2",
    "hojaDocumentoAdjuntada": "adjunta_doc_cobro",
    "pruebas": "pruebas",
}

QUEJA_MAP = {
    "tipoUsuario": "tipo_de_usuario_qja",
    "nombrePadre": "nombre_del_padre_abonado_qja",
    "nombreMadre": "nombre_de_la_madre_abonado_qja",
    "lugarNacimiento": "lugar_de_nacimiento_abonado_qja",
    "fechaNacimiento": "fecha_de_nacimiento_abonado_qja",
    "numeroDocumentIdentidad": "numero_documento_validacion_qja",
    "fechaEmisionDocumentoIdentidad": "fecha_emision_validacion_qja",
    "fechaVencimiento": "fecha_vencimiento_del_recibo_usuario_qja",
    "montoTarifa": "monto_de_tarifa_usuario_qja",
    "direccionFacturacion": "direccion_de_facturacion_usuario_qja",
    "tipoDocumentoIdentidad": "tipo_documento_identidad_qja",
    "nombre": "nombre_cliente_qja",
    "apellidos": "apellidos_qja",
    "relacion": "relacion_familiar_qja",
    "razonSocial": "razon_social_qja",
    "cartaPoder": "carta_de_poder_qja",
    "numeroContacto": "nro_contacto_qja",
    "tipoDoc": "tipo_doc_qja",
    "numDoc": "nro_documento_qja",
    "distritos": "distrito_cliente_qja",
    "direccion": "direccion_cliente_qja",
    "correo": "correo_electronico_qja",
    "booleanValue": "notificacion_por_correo_electronico_qja",
    "idQueja": "tipo_queja",
    "empresaOperadoraQueja": "empresa_operadora_ds1",
    "servicioObjetoQueja": "servicio_objeto_queja_dsq",
    "numServicioQueja": "nmero_servicio_reclamado_dsq",
    "codigoNumeroQueja": "cdigo_nmero_reclamo_dsq",
    "fechaPresentacionQueja": "fecha_presentacin_reclamo_queja_uno",
    "negativaQueja": "negativa_relacionada_queja_dos",
    "fechaNegativaQueja": "char_field_2bo_1ibhijmmb",
    "canalPresentacion": "canal_presentacin_reclamo_queja_dos",
    "especificarCanalQuejaDos": "canal_especificado_queja_dos",
    "fechaSuspendioServicioQueja": "fecha_en_la_cual_se_habra_suspendido_el_servicio",
    "MediosCobranzasQuejas": "medio_de_cobranza_queja_cuatro",
    "adjuntaPrueba": "se_adjunta_documento_queja_cuatro",
    "pagoCuentaQueja": "lugar_donde_permiti_pago_cinco",
    "espeficiarQueja": "especificar_quejas",
    "dtramitacion": "adjunta_medios_probatorios_x_seis",
    "capturaQuejaCinco": "adjunta_prueba_cinco",
    "informacionNecesariaQueja": "informacion_necesaria_queja",
    "descripcionProblemaQueja": "descripcion_problema_queja",
    # Archivos
    "constanciaPagoMedioCobranza": "vinculo_del_documento",
    "medioProbatoriopgQueja": "medio_probatorios_queja_ultimo",
    "medioProbatoriosTramitacion": "medios_probatorios",
    "medioProbatorioNegativa": "medios_probatorios_1",
    "pruebas": "pruebas",
}

APELACION_MAP = {
    "tipoUsuario": "tipo_de_usuario_ape",
    "nombrePadre": "nombre_del_padre_abonado_ape",
    "nombreMadre": "nombre_de_la_madre_abonado_ape",
    "lugarNacimiento": "lugar_de_nacimiento_abonado_ape",
    "fechaNacimiento": "fecha_de_nacimiento_abonado_ape",
    "numeroDocumentIdentidad": "numero_documento_identidad_ape",
    "fechaEmisionDocumentoIdentidad": "fecha_emision_documento_identidad_ape",
    "fechaVencimiento": "fecha_vencimiento_del_recibo_usuario_ape",
    "montoTarifa": "monto_de_tarifa_usuario_ape",
    "direccionFacturacion": "direccion_de_facturacion_usuario_ape",
    "tipoDocumentoIdentidad": "tipo_documento_identidad_ape",
    "nombre": "nombre_cliente_ape",
    "apellidos": "apellidos_ape",
    "relacion": "relacion_familiar_ape",
    "razonSocial": "razon_social_ape",
    "cartaPoder": "carta_de_poder_ape",
    "numeroContacto": "nro_contacto_ape",
    "tipoDoc": "tipo_doc_ape",
    "numDoc": "nro_documento_ape",
    "distritos": "distrito_cliente_ape",
    "direccion": "direccion_cliente_ape",
    "correo": "correo_electronico_ape",
    "booleanValue": "notificacion_por_correo_electronico_ape",
    "idApelacion": "tipo_apelacion",
    "empresaOperadoraApelacion": "empresa_operadora_ds",
    "servicioMateriaApelacion": "servicio_materia_de_apelacin_ds",
    "numeroServicioApelacion": "nmero_servicio_reclamado_ds",
    "codigoNumeroApelacion": "cdigo_nmero_reclamo_ds",
    "numeroCartaApelacion": "nmero_carta_resuelve_reclamo_ds",
    "fechaEmisionCartaApelacion": "fecha_emisin_carta_ds",
    "apelacionopcioncuatro": "respuesta_empresa_apelacion_cuatro",
    "numeroReciboApelacionSiCuatro": "numero_recibo_apelacion_cinco",
    "fechaEmisionApelacionSiCuatro": "fecha_de_emision",
    "fechaVencimientoApelacionSiCuatro": "fecha_de_vencimiento",
    "apelacionOpcioncinco": "falto_acoger_ape_cinco",
    "numeroReciboApelacionSiCinco": "nmero_recibo_apleacion_cinco",
    "fechaEmisionApelacionSiCinco": "fecha_de_emisin_1",
    "montoTotalApelacionSiCinco": "monto_total_corresponde_cinco",
    "informacionNecesariaApelacion": "informacin_necesaria_apelacion",
    "sustentoApelacion": "sustento_de_apelacin",
    "pruebas": "pruebas",
}

FIELD_MAPS = {
    "reclamosfp": RECLAMO_MAP,
    "quejasfp": QUEJA_MAP,
    "apelacionfp": APELACION_MAP,
}

# Campos que son archivos base64
FILE_FIELDS = {
    "reclamosfp": ["cartaPoder", "adjuntarVinculoSolicitud", "adjuntarVinculo",
                   "vinculoAdjuntarSolicitud", "vinculoSolicitudReclamo",
                   "adjuntarSolicitudReclamoCuatro", "solicitudBajaReclamo",
                   "hojaDocumentoAdjuntada", "pruebas"],
    "quejasfp": ["cartaPoder", "constanciaPagoMedioCobranza", "medioProbatoriopgQueja",
                 "medioProbatoriosTramitacion", "medioProbatorioNegativa", "pruebas"],
    "apelacionfp": ["cartaPoder", "pruebas"],
}

# Fechas a validar por modelo
DATE_FIELDS = {
    "reclamosfp": [
        "fechaEmisionDocumentoIdentidad", "fechaNacimiento", "fechaVencimiento",
        "fechaEmisionFC", "fechaVencimientoFC", "fechaEstimadaPagoFC",
        "fechaInicioCalidadI", "fechaIncumplimientos", "fechAproximadaIncumplimiento",
        "fechaCualPincumplimiento", "fechaEmisionIncumplimineto", "fechavencimientoIncumplimineto",
        "fechaInicioProblemafs", "fechaReactivarServicio", "fechaPagoPendiente",
        "fechaSIMCARD", "fechaContratacionServicioInstalacion", "fechaSolicitudTrasladoInstalacion",
        "fechaContratacionSInstalacion", "fechaSolicitudBaja", "fechaSolicitudSuspensionBaja",
        "fechaEmisionBaja", "fechaVencimientoBaja", "fechaEmisionContratacion",
        "fechaVencimientoContratacion", "fechaSolicitudMigracionX", "fechaEmisionMigracionIII",
        "fechaMovimientoMigracion", "fechaEmisionII", "fechaVencimientoMigracionII",
        "fechaEmisionMigracion", "fechaVencimientoMigracion", "fechaSolicitudX",
        "fechaEmisionX", "fechaVencimientoX", "fechaSolicitudFacturacionX",
    ],
    "quejasfp": [
        "fechaEmisionDocumentoIdentidad", "fechaPresentacionQueja", "fechaNegativaQueja",
        "fechaSuspendioServicioQueja", "fechaNacimiento", "fechaVencimiento",
    ],
    "apelacionfp": [
        "fechaEmisionDocumentoIdentidad", "fechaNacimiento", "fechaVencimiento",
        "fechaNegativaQueja", "fechaSuspendioServicioQueja", "fechaEmisionCartaApelacion",
        "fechaEmisionApelacionSiCuatro", "fechaVencimientoApelacionSiCuatro", "fechaEmisionApelacionSiCinco",
    ],
}

# Campos requeridos mínimos
REQUIRED_FIELDS = {
    "reclamosfp": [
        "tipoUsuario", "numeroDocumentIdentidad", "tipoDocumentoIdentidad",
        "nombre", "apellidos", "correo", "numeroContacto",
        "tipoDoc", "numDoc", "distritos", "direccion", "booleanValue",
        "idReclamo", "empresaOperadora", "servicioContratado", "numeroServicioContratado",
    ],
    "quejasfp": [
        "tipoUsuario", "numeroDocumentIdentidad", "tipoDocumentoIdentidad",
        "nombre", "apellidos", "correo", "numeroContacto",
        "tipoDoc", "numDoc", "distritos", "direccion", "booleanValue",
        "idQueja", "empresaOperadoraQueja", "servicioObjetoQueja", "numServicioQueja", "codigoNumeroQueja",
        "negativaQueja", "especificarCanalQuejaDos", "adjuntaPrueba",
        "MediosCobranzasQuejas", "pagoCuentaQueja", "espeficiarQueja",
        "dtramitacion", "informacionNecesariaQueja", "descripcionProblemaQueja", "capturaQuejaCinco",
    ],
    "apelacionfp": [
        "tipoUsuario", "nombrePadre", "nombreMadre", "lugarNacimiento", "fechaNacimiento",
        "fechaVencimiento", "montoTarifa", "direccionFacturacion",
        "numeroDocumentIdentidad", "tipoDocumentoIdentidad",
        "nombre", "apellidos", "relacion", "razonSocial", "numeroContacto",
        "tipoDoc", "numDoc", "distritos", "direccion", "correo", "booleanValue",
        "idApelacion", "empresaOperadoraApelacion", "servicioMateriaApelacion",
        "numeroServicioApelacion", "codigoNumeroApelacion", "numeroCartaApelacion", "fechaEmisionCartaApelacion",
        "apelacionopcioncuatro", "numeroReciboApelacionSiCuatro", "fechaEmisionApelacionSiCuatro",
        "fechaVencimientoApelacionSiCuatro", "apelacionOpcioncinco", "numeroReciboApelacionSiCinco",
        "fechaEmisionApelacionSiCinco", "montoTotalApelacionSiCinco",
        "informacionNecesariaApelacion", "sustentoApelacion",
    ],
}


def build_odoo_payload(data: dict, model: str, odoo_fields: set) -> Tuple[dict, list]:
    """Construye payload Odoo con mapeo completo. Retorna (payload, campos_desconocidos)."""
    field_map = FIELD_MAPS.get(model, {})
    payload = {"state": "draft", "medio_reclamo": "WEB"}
    unknown = []
    mapped = set()

    for front_key, odoo_key in field_map.items():
        if front_key not in data or data[front_key] is None:
            continue
        if odoo_key not in odoo_fields:
            unknown.append(front_key)
            continue
        payload[odoo_key] = data[front_key]
        mapped.add(front_key)

    # Loguear campos no mapeados que tienen valor
    for key in data:
        if key in mapped or data[key] in (None, "", [], {}):
            continue
        if key not in field_map:
            unknown.append(key)

    if unknown:
        logger.warning("Campos sin mapeo en %s: %s", model, unknown)

    return payload, unknown


def normalize_for_pdf(data: dict, model: str, ticket_name: str) -> dict:
    """Adapta el payload plano del frontend a la estructura que espera pdf_utils_osiptel_v2."""
    tipo_map = {"reclamosfp": "1", "quejasfp": "2", "apelacionfp": "3"}
    tipo = tipo_map.get(model, "1")

    doc_id = data.get("numDoc") or data.get("numeroDocumentIdentidad") or ""
    tipo_doc = data.get("tipoDoc") or data.get("tipoDocumentoIdentidad") or ""

    normalized = {
        "tipo": tipo,
        "ticket_number": ticket_name,
        "datos_generales": {
            "tipo_user": str(data.get("tipoUsuario", "")),
            "nombrescompletos": data.get("nombre", ""),
            "apellidoscompletos": data.get("apellidos", ""),
            "tipodocumento": tipo_doc,
            "numerodocumento": doc_id,
            "correoelectronico": data.get("correo", ""),
            "autorizacion": bool(data.get("booleanValue")),
            "distrito": data.get("distritos", ""),
            "direccioncasa": data.get("direccion", ""),
            "movil": data.get("numeroContacto", ""),
            "razonsocial": data.get("razonSocial", ""),
            "nombrePadre": data.get("nombrePadre", ""),
            "nombreMadre": data.get("nombreMadre", ""),
            "lugarNacimiento": data.get("lugarNacimiento", ""),
            "fechaNacimiento": data.get("fechaNacimiento", ""),
            "fechaEmisionDocumentoIdentidad": data.get("fechaEmisionDocumentoIdentidad", ""),
            "fechaVencimiento": data.get("fechaVencimiento", ""),
            "montoTarifa": data.get("montoTarifa", ""),
            "direccionFacturacion": data.get("direccionFacturacion", ""),
            "relacion": data.get("relacion", ""),
        },
        "empresa_operadora": data.get("empresaOperadora") or data.get("empresaOperadoraQueja") or data.get("empresaOperadoraApelacion", ""),
        "servicio_contratado": data.get("servicioContratado") or data.get("servicioObjetoQueja") or data.get("servicioMateriaApelacion", ""),
        "numero_servicio": data.get("numeroServicioContratado") or data.get("numServicioQueja") or data.get("numeroServicioApelacion", ""),
        "codigo_reclamo": data.get("codigoNumeroQueja") or data.get("codigoNumeroApelacion", ""),
        "archivos_adjuntos": [],
    }

    if model == "quejasfp":
        normalized["queja"] = {
            "idQueja": data.get("idQueja", ""),
            "fechaPresentacionQueja": data.get("fechaPresentacionQueja", ""),
            "negativaQueja": data.get("negativaQueja", ""),
            "fechaNegativaQueja": data.get("fechaNegativaQueja", ""),
            "canalPresentacion": data.get("canalPresentacion", ""),
            "especificarCanalQuejaDos": data.get("especificarCanalQuejaDos", ""),
            "medioProbatorioNegativa": "Adjuntado" if data.get("medioProbatorioNegativa") else "No adjuntado",
            "fechaSuspendioServicioQueja": data.get("fechaSuspendioServicioQueja", ""),
            "MediosCobranzasQuejas": data.get("MediosCobranzasQuejas", ""),
            "adjuntaPruebaBool": bool(data.get("adjuntaPrueba")),
            "constanciaPagoMedioCobranza": "Adjuntado" if data.get("constanciaPagoMedioCobranza") else "No adjuntado",
            "pagoCuentaQueja": data.get("pagoCuentaQueja", ""),
            "espeficiarQueja": data.get("espeficiarQueja", ""),
            "capturaQuejaBool": bool(data.get("capturaQuejaCinco")),
            "medioProbatoriopgQueja": "Adjuntado" if data.get("medioProbatoriopgQueja") else "No adjuntado",
            "tramitacionBool": bool(data.get("dtramitacion")),
            "medioProbatoriosTramitacion": "Adjuntado" if data.get("medioProbatoriosTramitacion") else "No adjuntado",
        }

    if model == "apelacionfp":
        normalized["apelacion"] = {
            "empresaOperadoraApelacion": data.get("empresaOperadoraApelacion", ""),
            "servicioMateriaApelacion": data.get("servicioMateriaApelacion", ""),
            "numeroServicioContratadoReclamo": data.get("numeroServicioApelacion", ""),
            "servicioMateriaReclamo": data.get("servicioMateriaApelacion", ""),
            "codigoNumeroApelacion": data.get("codigoNumeroApelacion", ""),
            "fechaEmisionCartaApelacion": data.get("fechaEmisionCartaApelacion", ""),
            "materiaEmpresaEmitirApelacionSeis": data.get("apelacionopcioncuatro", ""),
            "materiaEmpresaApelacionTres": data.get("apelacionOpcioncinco", ""),
        }

    # Archivos adjuntos (metadatos)
    file_fields = FILE_FIELDS.get(model, [])
    adjuntos = []
    for ff in file_fields:
        val = data.get(ff)
        if val and isinstance(val, str) and len(val) > 100:
            adjuntos.append(ff)
    normalized["archivos_adjuntos"] = adjuntos
    normalized["pruebas"] = data.get("pruebas") or data.get("cartaPoder") or None

    return normalized


def extract_email_attachments(data: dict, model: str) -> List[Tuple[str, str, bytes]]:
    """Extrae archivos base64 del payload como lista de (nombre, mime, bytes)."""
    from app.core.odoo_client import detect_name_type_from_base64, clean_base64
    attachments = []
    for field in FILE_FIELDS.get(model, []):
        raw = data.get(field)
        if not raw or not isinstance(raw, str):
            continue
        cleaned = clean_base64(raw)
        if not cleaned or len(cleaned) < 100:
            continue
        try:
            file_bytes = base64.b64decode(cleaned)
            name, mime = detect_name_type_from_base64(cleaned, default_name=field)
            attachments.append((name, mime, file_bytes))
        except Exception as e:
            logger.warning("No se pudo decodificar %s: %s", field, e)
    return attachments