# app/mappings.py
import base64
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("legal_mappings")

# =============================================================================
# MAPEO FRONTEND → ODOO (completo, por modelo)
# Reglas:
#  - Los campos se mapean tal cual llegan del HTML (ID/name).
#  - Los selects principales de tipo (idReclamo/idQueja/idApelacion) llegan como
#    strings ("fcs", "calidad", "apelacionOne", "quejaUno", etc.).
#  - Los archivos llegan como base64 con prefijo data:*.
#  - Los campos nuevos sin mapeo Odoo histórico se snake_casean y Odoo los
#    filtrará vía fields_get; se loguean como desconocidos.
# =============================================================================
# -----------------------------------------------------------------------------
# RECLAMO (reclamosfp) - sin sufijo
# -----------------------------------------------------------------------------
RECLAMO_MAP = {
    # --- Datos de validación (abonado / usuario) ---
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

    # --- Datos personales ---
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
    "autorizacion": "notificacion_por_correo_electronico",
    # alias booleanValue que usa el frontend en algunos flujos
    "booleanValue": "notificacion_por_correo_electronico",

    # --- Select principal + secundario ---
    "idReclamo": "materia_reclamable",
    "idReclamoEscogido": "problema_espec",

    # --- Datos del servicio (corregido: IDs reales del frontend) ---
    "empresaOperadora": "empresa_operadora_dsr",
    "servicioContratado": "servicio_contratado_dsr",
    "servicioMateriaReclamo": "servicio_materia_de_reclamo",
    "numeroServicioContratado": "nmero_cdigo_servicio_contrato_dsr",

    # --- FACTURACIÓN Y COBRO (fcs) ---
    "numeroReciboFCone": "numero_de_recibo",
    "numeroDocumentoCobroFCone": "documento_cobro",
    "fechaEmisionFCone": "fecha_de_emisin",
    "fechavencimientoFCone": "fecha_de_vencimiento_1",
    "montoReclamadoFCone": "monto_reclamado",
    "conceptoFacturadoFCone": "concepto_facturado",
    "tarifaUsuarioFCone": "tarifa_debio_aplicarse",
    "fechaEstimadaPagoFCone": "fecha_efectu_el_pago",
    "mPago": "modalidad_de_pago",
    "especificarModalidadPago": "especificar_modalidad_pago",
    "hpfacturado": "adjunta_recibo_pendiente2",
    "adjuntarHojaPagoFC": "adjunta_doc_cobro", #'adjunta_doc_cobro':hoja_fc,

    # --- CALIDAD E IDONEIDAD (calidad) ---
    "fechaInicioCalidadI": "fecha_de_inicio_del_problema_1",
    "direccionCalidadI": "direccin_presenta_problema",
    "departamentoCalidadI": "departamento",
    "provinciaCalidadI": "provincia",
    "distritoCalidad": "distrito_calidad",
    "calleJrAvCalidad": "calle_jr_av",
    "codigoReportePrevioCalidad": "codigo",

    # --- INCUMPLIMIENTO DE CONDICIONES (oferta) ---
    # Opción 1
    "detalleCondicionIncumplimiento": "detalle_condicin",
    "fechaIncumplimiento": "fecha_de_incumplimiento_1",
    # Opción 2
    "detalleOfertaIncumplimiento": "detalle_oferta_promocin_brindada",
    "oportunidadBrindoOfertaIncumplimiento": "oportunidad_en_el_cual_se_brindo_la_oferta_o_promocin",
    "fechAproximadaIncumplimiento": "fecha_aproximada_1",
    "cbpromocionfs": "canal_oferta_promocion",
    "especificarIncumplimiento": "especificar_canal",
    "codigOtorgamientoIncumplimiento": "cdigo_de_oferta_o_promocin",
    "fechaCualPincumplimiento": "fecha_se_presento_incumplimiento",
    # Opción 3
    "detalleAtributosIncumplimiento": "detalles_atributos_descontando",
    "reciboCorrespondienteIncumplimiento": "recibo_correspondiente_al_periodo",
    "fechaEmisionIncumplimineto": "fecha_de_emisin_del_recibo",
    "numeroRecivoIncumplimiento": "numero_de_recibo_tres",
    "fechavencimientoIncumplimineto": "fecha_de_vencimiento_6",
    # Opción 4
    #"detalleInfoOmitida": "oportunidad_brindo_informacin_inexacta",
    "oportunidadBrindoInfoOmitida": "oportunidad_brindo_informacin_inexacta",
    "fechaAproxInfoOmitida": "fecha_aproximada_2",
    #"cnPromocionCuatro": "canal_promocion_info_omitida",
    #"especificarInfoOmitida": "especificar_canal_info_omitida",

    # --- FALTA DE SERVICIO (falta) ---
    # Opción 1
    "fechaInicioProblemafs": "fecha_de_inicio_del_problema",
    "direccionProblemafs": "direccion_1",
    "departamentofs": "departamento_fs",
    "provinciafs": "provincia_fs",
    "distritofs": "distrito_fs",
    "calleJrAvfs": "calle_jr_av_fs",
    "numerofs": "numero_de_servicio",
    "adrecibos": "constancias_de_lugar_de_trabajo",
    "adjuntarVinculo": "documento",
    # Opción 2
    "direccionServicio": "direccin_problema",
    # Opción 3
    "fechaReactivarServicio": "fecha_que_corresponda_reactivar_el_servicio",
    "fechaPagoPendiente": "fecha_de_pago_pendiente",
    "mpagos": "lugar_medio_de_pago",
    "especificarMedioPago": "especificar_medio_pago",
    "adrecibosPendiente": "adjunta_recibo_pendiente",
    "vinculoAdjuntarSolicitud": "documento_1",
    # Opción 4
    "fechaSIMCARD": "fecha_que_se_ejecuto_el_cambio_sim_card",

    # --- INSTALACIÓN / ACTIVACIÓN / TRASLADO (instalacion) ---
    # Opción 1
    "fechaContratacionServicioInstalacion": "fecha_de_contratacin_de_servicio",
    # Opción 3
    "fechaSolicitudTrasladoInstalacion": "fecha_de_la_solicitud_de_traslado",
    "strasladoe": "canal_solicitud_traslado",
    "especificarCanalSinstalacion": "especificar_canal_2",
    "codigoPedidoII": "codigo_de_pedido",
    "adsOpcionTraslado": "se_adjunta_solicitud",
    "vinculoSolicitudReclamo": "vinculo_de_documento_adjuntado",
    # Opción 5
    "fechaContratacionSInstalacion": "fecha_de_la_contratacin_o_solicitud_de_trabajo",
    "ctopcionCinco": "canal_de_presentacin",
    "especificarInstalacion": "especificar_canal_3",
    "codigoPedidoInstalacion": "cdigo_de_pedido_2",
    "opcionCuatroTraslado": "adjuntar_solicitud_1",
    "adjuntarSolicitudReclamoCuatro": "vinculo_del_documento_adjuntado",
    "montoPendienteInstalacion": "monto_pendiente",

    # --- BAJA / SUSPENSIÓN (baja) ---
    # Opción 1
    "fechaSolicitudBaja": "fecha_de_la_solicitud_de_baja",
    "cbaja": "canal_presentacin_baja",
    "especificarCanalBaja": "especificar_canal_baja",
    "codigoPedidoBaja": "cdigo_de_pedido",
    "asb": "adjuntar_solicitud",
    "solicitudBajaReclamo": "vinculo_del_documento_2",
    # Opción 2
    "fechaSolicitudSuspensionBaja": "fecha_de_solicitud_de_suspensin_1",
    "ctraslado": "canal_traslado",
    "especificarCanalTraslado": "especificar_canal_1",
    "cPedidoBaja": "cdigo_de_pedido_1",
    "asT": "adjuntar_solicitud_suspensin",
    "adjuntarVinculoSolicitud": "vinculo_del_documento_1",
    # Opción 3/4
    "datosRecibosCuestionadoBaja": "datos_de_los_recibos_cuestionados",
    "numeroReciboBaja": "numero_de_recibo_1",
    "fechaEmisionBaja": "fecha_de_emisin_3",
    "fechaVencimientoBaja": "fecha_de_vencimiento_3",
    "montoReclamadoBaja": "monto_reclamado_3",

    # --- CONTRATACIÓN NO SOLICITADA (contratacion) ---
    # Base (conuno)
    "numeroReciboContratacion": "numero_de_recibo_no_solicitada",
    "fechaEmisionContratacion": "fecha_de_emisin_5",
    "fechaVencimientoContratacion": "fecha_de_vencimiento_5",
    "montoReclamadoContratacion": "monto_reclamado_no_solicitud",
    # Opción 2
    "detalleServicioAdicional": "detalle_adicional_no_solicitada",
    # Opción 3
    "detallePaquete": "detalle_paquete_desconoce",
    # Opción 4
    "datosRecibomrContatacion": "datos_recibos_cuestionados",

    # --- MIGRACIÓN (migracion) ---
    # Opción 1
    "fechaSolicitudMigracionX": "fecha_de_solicitud_de_migracin_1",
    "cmigracion": "canal_solicitud_de_migracin",
    "especificarCanalMigracion": "especificar_canal_de_solicitud",
    "codigoPedidoMigracion": "codigo_pedido_migracion",
    "planTarifarioMigracion": "plan_tarifario_solicita_migrar",
    "motivoNegativaMigracion": "motivo_de_la_negativa",
    "asm": "verificacion",
    "documentoSolicitudMigracionOne": "documento_de migracin",
    # Opción 2
    "numeroReciboMigracionII": "numero_recibo",
    "fechaEmisionMigracionIII": "fecha_de_emisin_2",
    "fechaMovimientoMigracion": "fecha_de_movimiento",
    "montoReclamadoMigracionMigracion": "monto_reclamado_1",
    # Opción 3
    "numeroReciboII": "numero_de_recibo_migracion",
    "fechaEmisionII": "fecha_emisin",
    "fechaVencimientoMigracionII": "fecha_de_vencimiento_2",
    # Opción 4
    "numeroReciboMigracion": "numero_recibo_migracin",
    "fechaEmisionMigracion": "fecha_de_emisin_migracin_1",
    "fechaVencimientoMigracion": "fecha_de_vencimiento_migracin_1",
    "montoReclamadoMigracion": "monto_reclamado_migracion",

    # --- OTRAS MATERIAS (xmaterias) ---
    # Opción 1
    "fechaSolicitudX": "fecha_de_la_solicitud_de_contratacion",
    "ccontratacion": "canal_solicitud_de_contratacion",
    #"especificarx": "especificarx",
    "servicioContratarX": "servicio_que_desea_contratar",
    "planTarifarioX": "plan_tarifario_que_desea_contratar",
    # Opción 2
    "numeroReciboX": "numero_de_recibo_x",
    "fechaEmisionX": "fecha_de_emisin_4",
    "fechaVencimientoX": "fecha_de_vencimiento_4",
    "mesReciboPentregaX": "mes_recibo_pendiente_entrega_x",
    "direccionFisicaX": "direccin_para_notificacin_x",
    # Opción 3
    "fechaSolicitudFacturacionX": "fecha_solicitud_facturacin_x",
    "cpresentacion": "canal_presentacin_solicitud_facturacion",
    "especificarCanalX": "especificar_canal_x",
    "codigoPedidoX": "cdigo_de_pedido_x",
    "sasfll": "se_adjunta_la_solicitud_x",
    "vinculoSolicitudSX": "documento_adjuntado_x",
    "detallePedidoX": "detalle_pedido_x",

    # --- Descargo del cliente ---
    "informacionNecesariaReclamo": "informacin_necesaria_reclamo",
    "descripcionProblemaSolicitudReclamo": "descripcin_problema_solicitud_concreta_reclamo",

    # --- Archivos genéricos (compatibilidad) ---
    "pruebas": "pruebas",
}

# -----------------------------------------------------------------------------
# QUEJA (quejasfp) - sufijo _qja
# -----------------------------------------------------------------------------
QUEJA_MAP = {
    # --- Datos de validación ---
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

    # --- Datos personales ---
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
    "autorizacion": "notificacion_por_correo_electronico_qja",
    "booleanValue": "notificacion_por_correo_electronico_qja",

    # --- Select principal + datos del servicio ---
    "idQueja": "tipo_queja",
    "empresaOperadoraQueja": "empresa_operadora_ds1",
    "servicioObjetoQueja": "servicio_objeto_queja_dsq",
    "numServicioQueja": "nmero_servicio_reclamado_dsq",
    "codigoNumeroQueja": "cdigo_nmero_reclamo_dsq",

    # --- Detalles adicionales por opción ---
    # quejaUno
    "fechaPresentacionQueja": "fecha_presentacin_reclamo_queja_uno",
    # quejaDos
    "negativaQueja": "negativa_relacionada_queja_dos",
    "fechaNegativaQueja": "char_field_2bo_1ibhijmmb",
    "canalPresentacion": "canal_presentacin_reclamo_queja_dos",
    "especificarCanalQuejaDos": "canal_especificado_queja_dos",
    #"adjuntaPrueba": "se_adjunta_medios_probatorios_queja_dos",
    #"medioProbatorioNegativa": "medio_probatorio_negativa_queja_dos",
    # quejaTres
    "fechaSuspendioServicioQueja": "fecha_en_la_cual_se_habra_suspendido_el_servicio",
    # quejaCuatro
    "MediosCobranzasQuejas": "medio_de_cobranza_queja_cuatro",
    #"constanciaPagoQueja": "documento_queja",
    #"constanciaPagoMedioCobranza": "constancia_pago_medio_cobranza_queja_cuatro",
    # quejaCinco
    "pagoCuentaQueja": "lugar_donde_permiti_pago_cinco",
    "espeficiarQueja": "especificar_quejas",
    "capturaQuejaCinco": "adjunta_prueba_cinco",
    #"medioProbatoriopgQueja": "medio_probatorio_pg_queja_cinco",
    # quejaSeis
    "dtramitacion": "adjunta_medios_probatorios_x_seis",
    #"medioProbatoriosTramitacion": "medios_probatorios_tramitacion_queja_seis",

    # --- Descargo del cliente ---
    "informacionNecesariaQueja": "informacion_necesaria_queja",
    "descripcionProblemaQueja": "descripcion_problema_queja",

    # --- Archivos genéricos ---
    "pruebas": "pruebas",
}

# -----------------------------------------------------------------------------
# APELACIÓN (apelacionfp) - sufijo _ape
# -----------------------------------------------------------------------------
APELACION_MAP = {
    # --- Datos de validación ---
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

    # --- Datos personales ---
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
    "autorizacion": "notificacion_por_correo_electronico_ape",
    "booleanValue": "notificacion_por_correo_electronico_ape",

    # --- Select principal + datos del servicio ---
    "idApelacion": "tipo_apelacion",
    "empresaOperadoraApelacion": "empresa_operadora_ds",
    "servicioMateriaApelacion": "servicio_materia_de_apelacin_ds",
    "numeroServicioApelacion": "nmero_servicio_reclamado_ds",
    "codigoNumeroApelacion": "cdigo_nmero_reclamo_ds",
    "numeroCartaApelacion": "nmero_carta_resuelve_reclamo_ds",
    "fechaEmisionCartaApelacion": "fecha_emisin_carta_ds",

    # --- Detalles adicionales por tipo de apelación ---
    # apelacionOne
    "detallePruebaApelacionUno": "detalle_pruebaS_apelacion_uno",
    # apelacionTwo
    "detallefsApelacionDos": "detalle_falta_sustentacion_apelacion_dos",
    # apelacionThree
    "materiaEmpresaApelacionTres": "materia_empresa_comunicarse",
    # apelacionFour (si/no)
    "apelacionopcioncuatro": "respuesta_empresa_apelacion_cuatro",
    "numeroReciboApelacionSiCuatro": "numero_recibo_apelacion_cinco",
    "fechaEmisionApelacionSiCuatro": "fecha_de_emision",
    "fechaVencimientoApelacionSiCuatro": "fecha_de_vencimiento",
    #"montoReclamadoApelacionSiCuatro": "monto_reclamado_apelacion_si_cuatro",
    "detalleReclamoApelacionSiCuatro": "pronunciamiento_empresa_ape_cuatro",
    # apelacionFive (si/no)
    "apelacionOpcioncinco": "falto_acoger_ape_cinco",
    "numeroReciboApelacionSiCinco": "nmero_recibo_apleacion_cinco",
    "fechaEmisionApelacionSiCinco": "fecha_de_emisin_1",
    "montoTotalApelacionSiCinco": "monto_total_corresponde_cinco",
    "detalleReclamoApelacionSiCinco": "detalle_extremo_apelacion_cinco",
    # apelacionSix
    "materiaEmpresaEmitirApelacionSeis": "materia_cual_empresa_ape_seis",

    # --- Descargo del cliente ---
    "informacionNecesariaApelacion": "informacin_necesaria_apelacion",
    "sustentoApelacion": "sustento_de_apelacin",

    # --- Archivos genéricos ---
    "pruebas": "pruebas",
}

FIELD_MAPS: Dict[str, Dict[str, str]] = {
    "reclamosfp": RECLAMO_MAP,
    "quejasfp": QUEJA_MAP,
    "apelacionfp": APELACION_MAP,
}

# -----------------------------------------------------------------------------
# CAMPOS DE ARCHIVO (type="file") por modelo
# -----------------------------------------------------------------------------
FILE_FIELDS: Dict[str, List[str]] = {
    "reclamosfp": [
        "cartaPoder",                      # representante
        "adjuntarHojaPagoFC",                 # fcs (si hpfacturado=si)
        "adjuntarVinculo",                 # falta opción 1
        "vinculoAdjuntarSolicitud",        # falta opción 3
        "vinculoSolicitudReclamo",         # instalación opción 3
        "adjuntarSolicitudReclamoCuatro",  # instalación opción 5
        "solicitudBajaReclamo",            # baja opción 1
        "adjuntarVinculoSolicitud",        # baja opción 2
        "documentoSolicitudMigracionOne",  # migración opción 1
        "vinculoSolicitudSX",              # xmaterias opción 3
        "pruebas",
    ],
    "quejasfp": [
        "cartaPoder",
        "medioProbatorioNegativa",        # quejaDos
        "constanciaPagoMedioCobranza",    # quejaCuatro
        "medioProbatoriopgQueja",         # quejaCinco
        "medioProbatoriosTramitacion",    # quejaSeis
        "pruebas",
    ],
    "apelacionfp": [
        "cartaPoder",
        "pruebas",
    ],
}

# -----------------------------------------------------------------------------
# CAMPOS DE FECHA por modelo (todos los type="date" del HTML)
# -----------------------------------------------------------------------------
DATE_FIELDS: Dict[str, List[str]] = {
    "reclamosfp": [
        # validación
        "fechaEmisionDocumentoIdentidad", "fechaNacimiento", "fechaVencimiento",
        # fcs
        "fechaEmisionFCone", "fechavencimientoFCone", "fechaEstimadaPagoFCone",
        # calidad
        "fechaInicioCalidadI",
        # incumplimiento
        "fechaIncumplimiento", "fechAproximadaIncumplimiento",
        "fechaCualPincumplimiento", "fechaEmisionIncumplimineto",
        "fechavencimientoIncumplimineto", "fechaAproxInfoOmitida",
        # falta servicio
        "fechaInicioProblemafs", "fechaReactivarServicio", "fechaPagoPendiente",
        "fechaSIMCARD",
        # instalación
        "fechaContratacionServicioInstalacion", "fechaSolicitudTrasladoInstalacion",
        "fechaContratacionSInstalacion",
        # baja
        "fechaSolicitudBaja", "fechaSolicitudSuspensionBaja",
        "fechaEmisionBaja", "fechaVencimientoBaja",
        # contratación
        "fechaEmisionContratacion", "fechaVencimientoContratacion",
        # migración
        "fechaSolicitudMigracionX", "fechaEmisionMigracionIII",
        "fechaMovimientoMigracion", "fechaEmisionII",
        "fechaVencimientoMigracionII", "fechaEmisionMigracion",
        "fechaVencimientoMigracion",
        # xmaterias
        "fechaSolicitudX", "fechaEmisionX", "fechaVencimientoX",
        "fechaSolicitudFacturacionX",
    ],
    "quejasfp": [
        "fechaEmisionDocumentoIdentidad", "fechaNacimiento", "fechaVencimiento",
        "fechaPresentacionQueja",
        "fechaNegativaQueja",
        "fechaSuspendioServicioQueja",
    ],
    "apelacionfp": [
        "fechaEmisionDocumentoIdentidad", "fechaNacimiento", "fechaVencimiento",
        "fechaEmisionCartaApelacion",
        "fechaEmisionApelacionSiCuatro",
        "fechaVencimientoApelacionSiCuatro",
        "fechaEmisionApelacionSiCinco",
    ],
}

# -----------------------------------------------------------------------------
# CAMPOS REQUERIDOS por modelo
# Solo los que tienen `required` en HTML + los selects principales de tipo.
# Los condicionales (display:none) NO se incluyen aquí; se validan en runtime
# según el idReclamo/idQueja/idApelacion elegido.
# -----------------------------------------------------------------------------
REQUIRED_FIELDS: Dict[str, List[str]] = {
    "reclamosfp": [
        # personales con `required`
        "name",
        "apellidos",
        "numeroContacto",
        "tipoDoc",
        "numDoc",
        "distritos",
        "direccion",
        "correo",
        # selects principales
        "idReclamo",
        # datos del servicio (no tienen `required` pero son obligatorios de flujo)
        "empresaOperadora",
        "servicioContratado",
        "servicioMateriaReclamo",
        "numeroServicioContratado",
    ],
    "quejasfp": [
        "name",
        "apellidos",
        "numeroContacto",
        "tipoDoc",
        "numDoc",
        "distritos",
        "direccion",
        "correo",
        "idQueja",
        "empresaOperadoraQueja",
        "servicioObjetoQueja",
        "numServicioQueja",
        "codigoNumeroQueja",
    ],
    "apelacionfp": [
        "name",
        "apellidos",
        "numeroContacto",
        "tipoDoc",
        "numDoc",
        "distritos",
        "direccion",
        "correo",
        "idApelacion",
        "empresaOperadoraApelacion",
        "servicioMateriaApelacion",
        "numeroServicioApelacion",
        "codigoNumeroApelacion",
        "numeroCartaApelacion",
        "fechaEmisionCartaApelacion",
    ],
}

# Alias frontend → clave canónica usada en REQUIRED_FIELDS y en el payload plano
# (el frontend a veces envía "name" y a veces "nombre"; "direccion"/"correo"
# pueden venir agrupados bajo name="datosPersonales").
FRONTEND_ALIAS = {
    "name": "name",
    "nombre": "name",
    "apellidos": "apellidos",
    "numeroContacto": "numeroContacto",
    "tipoDoc": "tipoDoc",
    "numDoc": "numDoc",
    "distritos": "distritos",
    "direccion": "direccion",
    "correo": "correo",
}

def _resolve_alias(key: str) -> str:
    return FRONTEND_ALIAS.get(key, key)

# =============================================================================
# FUNCIONES PRINCIPALES
# =============================================================================

def build_odoo_payload(data: dict, model: str, odoo_fields: set) -> Tuple[dict, list]:
    """
    Construye payload Odoo con mapeo completo.
    Retorna (payload, campos_desconocidos).

    - data: payload plano recibido del frontend.
    - model: 'reclamosfp' | 'quejasfp' | 'apelacionfp'.
    - odoo_fields: set de nombres de campo válidos en el modelo Odoo (vía fields_get).
    """
    field_map = FIELD_MAPS.get(model, {})
    #payload = {"state": "draft", "medio_reclamo": "WEB"}
    payload = {}
    # unknown: List[str] = []
    # mapped = set()
    
    if "state" in odoo_fields:
        payload["state"] = "draft"
    
    # Añadir medio_reclamo solo si existe en Odoo
    if "medio_reclamo" in odoo_fields:
        payload["medio_reclamo"] = "WEB"
    
    unknown: List[str] = []
    mapped = set()

    for front_key, odoo_key in field_map.items():
        if front_key not in data or data[front_key] in (None, ""):
            continue
        if odoo_key not in odoo_fields:
            unknown.append(front_key)
            continue
        payload[odoo_key] = data[front_key]
        mapped.add(front_key)

    # Detectar campos con valor que no están en el mapa
    for key, val in data.items():
        if key in mapped or val in (None, "", [], {}):
            continue
        if key not in field_map:
            unknown.append(key)

    if unknown:
        logger.warning("Campos sin mapeo en %s: %s", model, sorted(set(unknown)))

    return payload, unknown

def normalize_for_pdf(data: dict, model: str, ticket_name: str) -> dict:
    """
    Adapta el payload plano del frontend a la estructura que espera
    pdf_utils_osiptel_v2. Incluye TODOS los campos del frontend en
    datos_generales / datos_especificos para que el PDF sea completo.
    """
    tipo_map = {"reclamosfp": "1", "quejasfp": "2", "apelacionfp": "3"}
    tipo = tipo_map.get(model, "1")

    doc_id = data.get("numDoc") or data.get("numeroDocumentIdentidad") or ""
    tipo_doc = data.get("tipoDoc") or data.get("tipoDocumentoIdentidad") or ""

    # Datos personales (comunes)
    datos_generales = {
        "tipo_user": str(data.get("tipoUsuario", "")),
        "nombrescompletos": data.get("name") or data.get("nombre", ""),
        "apellidoscompletos": data.get("apellidos", ""),
        "tipodocumento": tipo_doc,
        "numerodocumento": doc_id,
        "correoelectronico": data.get("correo", ""),
        "autorizacion": bool(data.get("autorizacion", data.get("booleanValue"))),
        "distrito": data.get("distritos", ""),
        "direccioncasa": data.get("direccion", ""),
        "movil": data.get("numeroContacto", ""),
        "razonsocial": data.get("razonSocial", ""),
        "relacion": data.get("relacion", ""),

        # Validación - abonado
        "nombrePadre": data.get("nombrePadre", ""),
        "nombreMadre": data.get("nombreMadre", ""),
        "lugarNacimiento": data.get("lugarNacimiento", ""),
        "fechaNacimiento": data.get("fechaNacimiento", ""),
        "fechaEmisionDocumentoIdentidad": data.get("fechaEmisionDocumentoIdentidad", ""),

        # Validación - usuario
        "fechaVencimiento": data.get("fechaVencimiento", ""),
        "montoTarifa": data.get("montoTarifa", ""),
        "direccionFacturacion": data.get("direccionFacturacion", ""),
        "tipoDocumentoIdentidad": data.get("tipoDocumentoIdentidad", ""),
    }

    normalized: dict = {
        "tipo": tipo,
        "ticket_number": ticket_name,
        "datos_generales": datos_generales,
        "archivos_adjuntos": [],
    }

    # ------------------------------------------------------------------
    # RECLAMO: todos los campos por materia
    # ------------------------------------------------------------------
    if model == "reclamosfp":
        normalized["empresa_operadora"] = data.get("empresaOperadora", "")
        normalized["servicio_contratado"] = data.get("servicioContratado", "")
        normalized["servicio_materia"] = data.get("servicioMateriaReclamo", "")
        normalized["numero_servicio"] = data.get("numeroServicioContratado", "")
        normalized["idReclamo"] = data.get("idReclamo", "")
        normalized["idReclamoEscogido"] = data.get("idReclamoEscogido", "")

        # TODOS los campos específicos por materia se copian tal cual
        # (el generador PDF puede decidir cuáles mostrar según idReclamo/idReclamoEscogido)
        reclamo_detail_keys = [
            # fcs
            "numeroReciboFCone", "numeroDocumentoCobroFCone", "fechaEmisionFCone",
            "fechavencimientoFCone", "montoReclamadoFCone", "conceptoFacturadoFCone",
            "tarifaUsuarioFCone", "fechaEstimadaPagoFCone", "mPago",
            "especificarModalidadPago", "hpfacturado", "adjuntarHojaPagoFC",
            # calidad
            "fechaInicioCalidadI", "direccionCalidadI", "departamentoCalidadI",
            "provinciaCalidadI", "distritoCalidad", "calleJrAvCalidad",
            "codigoReportePrevioCalidad",
            # incumplimiento 1
            "detalleCondicionIncumplimiento", "fechaIncumplimiento",
            # incumplimiento 2
            "detalleOfertaIncumplimiento", "oportunidadBrindoOfertaIncumplimiento",
            "fechAproximadaIncumplimiento", "cbpromocionfs", "especificarIncumplimiento",
            "codigOtorgamientoIncumplimiento", "fechaCualPincumplimiento",
            # incumplimiento 3
            "detalleAtributosIncumplimiento", "reciboCorrespondienteIncumplimiento",
            "fechaEmisionIncumplimineto", "numeroRecivoIncumplimiento",
            "fechavencimientoIncumplimineto",
            # incumplimiento 4
            "detalleInfoOmitida", "oportunidadBrindoInfoOmitida",
            "fechaAproxInfoOmitida", "cnPromocionCuatro", "especificarInfoOmitida",
            # falta 1
            "fechaInicioProblemafs", "direccionProblemafs", "departamentofs",
            "provinciafs", "distritofs", "calleJrAvfs", "numerofs",
            "adrecibos", "adjuntarVinculo",
            # falta 2
            "direccionServicio",
            # falta 3
            "fechaReactivarServicio", "fechaPagoPendiente", "mpagos",
            "especificarMedioPago", "adrecibosPendiente", "vinculoAdjuntarSolicitud",
            # falta 4
            "fechaSIMCARD",
            # instalación 1
            "fechaContratacionServicioInstalacion",
            # instalación 3
            "fechaSolicitudTrasladoInstalacion", "strasladoe",
            "especificarCanalSinstalacion", "codigoPedidoII",
            "adsOpcionTraslado", "vinculoSolicitudReclamo",
            # instalación 5
            "fechaContratacionSInstalacion", "ctopcionCinco", "especificarInstalacion",
            "codigoPedidoInstalacion", "opcionCuatroTraslado",
            "adjuntarSolicitudReclamoCuatro", "montoPendienteInstalacion",
            # baja 1
            "fechaSolicitudBaja", "cbaja", "especificarCanalBaja",
            "codigoPedidoBaja", "asb", "solicitudBajaReclamo",
            # baja 2
            "fechaSolicitudSuspensionBaja", "ctraslado", "especificarCanalTraslado",
            "cPedidoBaja", "asT", "adjuntarVinculoSolicitud",
            # baja 3/4
            "datosRecibosCuestionadoBaja", "numeroReciboBaja",
            "fechaEmisionBaja", "fechaVencimientoBaja", "montoReclamadoBaja",
            # contratación base
            "numeroReciboContratacion", "fechaEmisionContratacion",
            "fechaVencimientoContratacion", "montoReclamadoContratacion",
            # contratación 2/3/4
            "detalleServicioAdicional", "detallePaquete", "datosRecibomrContatacion",
            # migración 1
            "fechaSolicitudMigracionX", "cmigracion", "especificarCanalMigracion",
            "codigoPedidoMigracion", "planTarifarioMigracion",
            "motivoNegativaMigracion", "asm", "documentoSolicitudMigracionOne",
            # migración 2
            "numeroReciboMigracionII", "fechaEmisionMigracionIII",
            "fechaMovimientoMigracion", "montoReclamadoMigracionMigracion",
            # migración 3
            "numeroReciboII", "fechaEmisionII", "fechaVencimientoMigracionII",
            # migración 4
            "numeroReciboMigracion", "fechaEmisionMigracion",
            "fechaVencimientoMigracion", "montoReclamadoMigracion",
            # xmaterias 1
            "fechaSolicitudX", "ccontratacion", "especificarx",
            "servicioContratarX", "planTarifarioX",
            # xmaterias 2
            "numeroReciboX", "fechaEmisionX", "fechaVencimientoX",
            "mesReciboPentregaX", "direccionFisicaX",
            # xmaterias 3
            "fechaSolicitudFacturacionX", "cpresentacion", "especificarCanalX",
            "codigoPedidoX", "sasfll", "vinculoSolicitudSX", "detallePedidoX",
            # descargo
            "informacionNecesariaReclamo", "descripcionProblemaSolicitudReclamo",
        ]
        normalized["reclamo"] = {k: data.get(k, "") for k in reclamo_detail_keys}

    # ------------------------------------------------------------------
    # QUEJA
    # ------------------------------------------------------------------
    if model == "quejasfp":
        normalized["empresa_operadora"] = data.get("empresaOperadoraQueja", "")
        normalized["servicio_contratado"] = data.get("servicioObjetoQueja", "")
        normalized["numero_servicio"] = data.get("numServicioQueja", "")
        normalized["codigo_reclamo"] = data.get("codigoNumeroQueja", "")

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
            "constanciaPagoQueja": data.get("constanciaPagoQueja", ""),
            "constanciaPagoMedioCobranza": "Adjuntado" if data.get("constanciaPagoMedioCobranza") else "No adjuntado",
            "pagoCuentaQueja": data.get("pagoCuentaQueja", ""),
            "espeficiarQueja": data.get("espeficiarQueja", ""),
            "capturaQuejaCinco": data.get("capturaQuejaCinco", ""),
            "medioProbatoriopgQueja": "Adjuntado" if data.get("medioProbatoriopgQueja") else "No adjuntado",
            "dtramitacion": data.get("dtramitacion", ""),
            "medioProbatoriosTramitacion": "Adjuntado" if data.get("medioProbatoriosTramitacion") else "No adjuntado",
            "informacionNecesariaQueja": data.get("informacionNecesariaQueja", ""),
            "descripcionProblemaQueja": data.get("descripcionProblemaQueja", ""),
        }

    # ------------------------------------------------------------------
    # APELACIÓN
    # ------------------------------------------------------------------
    if model == "apelacionfp":
        normalized["empresa_operadora"] = data.get("empresaOperadoraApelacion", "")
        normalized["servicio_contratado"] = data.get("servicioMateriaApelacion", "")
        normalized["numero_servicio"] = data.get("numeroServicioApelacion", "")
        normalized["codigo_reclamo"] = data.get("codigoNumeroApelacion", "")

        normalized["apelacion"] = {
            "idApelacion": data.get("idApelacion", ""),
            "numeroCartaApelacion": data.get("numeroCartaApelacion", ""),
            "fechaEmisionCartaApelacion": data.get("fechaEmisionCartaApelacion", ""),
            # apelacionOne
            "detallePruebaApelacionUno": data.get("detallePruebaApelacionUno", ""),
            # apelacionTwo
            "detallefsApelacionDos": data.get("detallefsApelacionDos", ""),
            # apelacionThree
            "materiaEmpresaApelacionTres": data.get("materiaEmpresaApelacionTres", ""),
            # apelacionFour
            "apelacionopcioncuatro": data.get("apelacionopcioncuatro", ""),
            "numeroReciboApelacionSiCuatro": data.get("numeroReciboApelacionSiCuatro", ""),
            "fechaEmisionApelacionSiCuatro": data.get("fechaEmisionApelacionSiCuatro", ""),
            "fechaVencimientoApelacionSiCuatro": data.get("fechaVencimientoApelacionSiCuatro", ""),
            "montoReclamadoApelacionSiCuatro": data.get("montoReclamadoApelacionSiCuatro", ""),
            "detalleReclamoApelacionSiCuatro": data.get("detalleReclamoApelacionSiCuatro", ""),
            # apelacionFive
            "apelacionOpcioncinco": data.get("apelacionOpcioncinco", ""),
            "numeroReciboApelacionSiCinco": data.get("numeroReciboApelacionSiCinco", ""),
            "fechaEmisionApelacionSiCinco": data.get("fechaEmisionApelacionSiCinco", ""),
            "montoTotalApelacionSiCinco": data.get("montoTotalApelacionSiCinco", ""),
            "detalleReclamoApelacionSiCinco": data.get("detalleReclamoApelacionSiCinco", ""),
            # apelacionSix
            "materiaEmpresaEmitirApelacionSeis": data.get("materiaEmpresaEmitirApelacionSeis", ""),
            # descargo
            "informacionNecesariaApelacion": data.get("informacionNecesariaApelacion", ""),
            "sustentoApelacion": data.get("sustentoApelacion", ""),
        }

    # Metadatos de archivos adjuntos (nombres de campos con base64 válido)
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
    """
    Extrae archivos base64 del payload como lista de (nombre, mime, bytes).
    Recorre FILE_FIELDS[model] y decodifica los que tengan contenido válido.
    """
    from app.core.odoo_client import detect_name_type_from_base64, clean_base64

    attachments: List[Tuple[str, str, bytes]] = []
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