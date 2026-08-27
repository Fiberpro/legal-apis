import os
from fpdf import FPDF
import tempfile
from zoneinfo import ZoneInfo
from datetime import datetime

ZoneInfo("America/Lima")

def clean_text(txt):
    """Limpia texto para FPDF (encoding latin-1)."""
    if txt is None:
        return ""
    txt = str(txt)
    replacements = {
        "–": "-", "—": "-", "“": '"', "”": '"',
        "‘": "'", "’": "'", "•": "-", "°": "o",
        "…": "...", "©": "(c)", "®": "(R)", "\xa0": " ",
        "ñ": "n", "Ñ": "N", "á": "a", "é": "e", "í": "i",
        "ó": "o", "ú": "u", "Á": "A", "É": "E", "Í": "I",
        "Ó": "O", "Ú": "U", "ü": "u", "Ü": "U",
    }
    for bad, good in replacements.items():
        txt = txt.replace(bad, good)
    return txt.encode("latin-1", "replace").decode("latin-1").strip()

class PDFConstancia(FPDF):
    def __init__(self, tipo_ticket="1", ticket_number=""):
        super().__init__()
        self.tipo_ticket = str(tipo_ticket)
        self.ticket_number = str(ticket_number)

    def header(self):
        # Logoo
        try:
            self.image("static/logo.png", x=10, y=8, w=45)
        except Exception:
            pass

        titulo_map = {
            "1": "FORMULARIO DE RECLAMO",
            "2": "FORMULARIO DE QUEJA",
            "3": "FORMULARIO DE RECURSO DE APELACION"
        }
        titulo = titulo_map.get(self.tipo_ticket, "FORMULARIO LEGAL")

        self.set_xy(60, 8)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, clean_text(titulo), 0, 1, "L")

        # Recuadro de ticket
        if self.ticket_number:
            self.set_xy(140, 22)
            self.set_font("Arial", "B", 10)
            self.set_fill_color(230, 230, 230)
            self.cell(60, 8, clean_text(f"N Ticket: {self.ticket_number}"), 1, 0, "C", True)

        # Linea separadora
        self.set_xy(10, 36)
        self.set_line_width(0.5)
        self.line(10, 36, 200, 36)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, clean_text(f"Generado automaticamente - {fecha}"), align="C")

    def bloque_titulo(self, titulo):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(220, 220, 220)
        self.cell(0, 8, clean_text(titulo), 0, 1, "L", True)
        self.ln(2)

    def fila(self, etiqueta, valor):
        self.set_font("Arial", "B", 10)
        self.cell(60, 6, clean_text(etiqueta), 0, 0, "L")
        self.set_font("Arial", "", 10)
        self.cell(0, 6, clean_text(valor), 0, 1, "L")
        self.ln(1)

    def fila_doble(self, e1, v1, e2, v2):
        x0 = self.get_x()
        y0 = self.get_y()
        page_w = self.w - self.l_margin - self.r_margin
        label_w = 40
        val_w = (page_w - 2 * label_w) / 2
        line_h = 5
        # Columna 1: etiqueta 1 (con wrap)
        self.set_xy(x0, y0)
        self.set_font("Arial", "B", 10)
        self.multi_cell(label_w, line_h, clean_text(e1), 0, "L")
        h1_label = self.get_y() - y0
        # Columna 2: valor 1 (con wrap)
        self.set_font("Arial", "", 10)
        self.set_xy(x0 + label_w, y0)
        self.multi_cell(val_w, line_h, clean_text(v1), 0, "L")
        h1_val = self.get_y() - y0
        # Columna 3: etiqueta 2 (con wrap, al costado del primer par)
        self.set_xy(x0 + label_w + val_w, y0)
        self.set_font("Arial", "B", 10)
        self.multi_cell(label_w, line_h, clean_text(e2), 0, "L")
        h2_label = self.get_y() - y0
        # Columna 4: valor 2 (con wrap, ancho hasta el margen derecho)
        self.set_font("Arial", "", 10)
        val2_w = self.w - self.r_margin - (x0 + label_w + val_w + label_w)
        self.set_xy(x0 + label_w + val_w + label_w, y0)
        self.multi_cell(val2_w, line_h, clean_text(v2), 0, "L")
        h2_val = self.get_y() - y0
        # Avanzar al maximo entre las 4 columnas
        self.set_y(y0 + max(h1_label, h1_val, h2_label, h2_val, 6))
        self.ln(1)

    def caja(self, etiqueta, valor=""):
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, clean_text(etiqueta), 1, 1, "L")
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 6, clean_text(valor), 1, "L")
        self.ln(2)

def generar_pdf(data):
    """
    Genera constancia PDF para Reclamo, Queja o Apelacion.
    
    Args:
        data: dict con estructura normalizada desde app.mappings.normalize_for_pdf()
              {
                "tipo": "1"|"2"|"3",
                "ticket_number": "...",
                "datos_generales": {...},
                "queja": {...},          # solo tipo 2
                "apelacion": {...},      # solo tipo 3
                "archivos_adjuntos": [...],
                "empresa_operadora": "...",
                "servicio_contratado": "...",
                ...
              }
    
    Returns:
        str: ruta al archivo PDF temporal
    """
    tipo = str(data.get("tipo", "1"))
    ticket = data.get("ticket_number", "")
    pdf = PDFConstancia(tipo_ticket=tipo, ticket_number=ticket)
    pdf.add_page()

    d = data.get("datos_generales", {})
    tipo_user_map = {"1": "Abonado", "abonado": "Abonado",
                     "2": "Usuario", "usuario": "Usuario",
                     "3": "Representante", "representante": "Representante",}

    # =====================================================
    # 1. DATOS DEL RECLAMANTE
    # =====================================================
    pdf.bloque_titulo("1. DATOS DEL RECLAMANTE")
    tipo_user_raw = d.get("tipo_user")
    tipo_user_key = str(tipo_user_raw).strip().lower() if tipo_user_raw is not None else ""
    pdf.fila("Condicion de quien presenta", tipo_user_map.get(tipo_user_key, "-"))
    pdf.fila_doble("Nombres", d.get("nombrescompletos", ""), "Apellidos", d.get("apellidoscompletos", ""))
    pdf.fila("Razon social", d.get("razonsocial", "") or "-")
    pdf.fila_doble("Tipo de documento", d.get("tipodocumento", ""), "N documento", d.get("numerodocumento", ""))

    # =====================================================
    # 2. DATOS DE VALIDACION
    # =====================================================
    tiene_validacion = any([
        d.get("nombrePadre"), d.get("nombreMadre"), d.get("lugarNacimiento"),
        d.get("fechaNacimiento"), d.get("fechaEmisionDocumentoIdentidad"),
        d.get("relacion"), d.get("fechaVencimiento"), d.get("montoTarifa"),
        d.get("direccionFacturacion")
    ])
    if tiene_validacion:
        pdf.bloque_titulo("2. DATOS DE VALIDACION")
        if d.get("nombrePadre") or d.get("nombreMadre"):
            pdf.fila_doble("Nombre del padre", d.get("nombrePadre", "-"), "Nombre de la madre", d.get("nombreMadre", "-"))
        if d.get("lugarNacimiento") or d.get("fechaNacimiento"):
            pdf.fila_doble("Lugar de nacimiento", d.get("lugarNacimiento", "-"), "Fecha de nacimiento", d.get("fechaNacimiento", "-"))
        if d.get("fechaEmisionDocumentoIdentidad") or d.get("relacion"):
            pdf.fila_doble("Fecha emision documento", d.get("fechaEmisionDocumentoIdentidad", "-"), "Relacion familiar", d.get("relacion", "-"))
        if d.get("fechaVencimiento") or d.get("montoTarifa"):
            pdf.fila_doble("Fecha vencimiento recibo", d.get("fechaVencimiento", "-"), "Monto de tarifa", d.get("montoTarifa", "-"))
        if d.get("direccionFacturacion"):
            pdf.fila("Direccion de facturacion", d.get("direccionFacturacion", "-"))

    # =====================================================
    # 3. CONTACTO Y NOTIFICACION
    # =====================================================
    pdf.bloque_titulo("3. DATOS PARA LA NOTIFICACION Y CONTACTO")

    pdf.fila_doble("Correo electronico", d.get("correoelectronico", ""), "Autoriza notificacion", "Si" if d.get("autorizacion") else "No")
    pdf.fila_doble("Distrito", d.get("distrito", ""), "Direccion", d.get("direccioncasa", ""))
    pdf.fila("Telefono / Movil", d.get("movil", "") or "-")

    # =====================================================
    # 4. DATOS DEL SERVICIO
    # =====================================================
    pdf.bloque_titulo("4. DATOS DEL SERVICIO")
    # pdf.fila_doble("Empresa operadora", data.get("empresa_operadora", "-"), "Servicio contratado", data.get("servicio_contratado", "-"))
    # pdf.fila_doble("N servicio / contrato", data.get("numero_servicio", "-"), "Codigo de reclamo", data.get("codigo_reclamo", "-"))
    if tipo == "3" and data.get("apelacion"):
        a = data.get("apelacion", {})
        pdf.fila_doble(
            "Empresa operadora",
            a.get("empresaOperadoraApelacion") or data.get("empresa_operadora", "-"),
            "Servicio materia apelacion",
            a.get("servicioMateriaApelacion") or data.get("servicio_contratado", "-"),
        )
        pdf.fila_doble(
            "N servicio / contrato",
            a.get("numeroServicioContratadoReclamo") or data.get("numero_servicio", "-"),
            "Codigo de reclamo",
            a.get("codigoNumeroApelacion") or data.get("codigo_reclamo", "-"),
        )
        pdf.fila_doble(
            "N carta resuelve reclamo",
            a.get("numeroCartaApelacion", "-"),
            "Fecha emision carta",
            a.get("fechaEmisionCartaApelacion", "-"),
        )
    else:
        pdf.fila_doble(
            "Empresa operadora",
            data.get("empresa_operadora", "-"),
            "Servicio contratado",
            data.get("servicio_contratado", "-"),
        )
        pdf.fila_doble(
            "N servicio / contrato",
            data.get("numero_servicio", "-"),
            "Codigo de reclamo",
            data.get("codigo_reclamo", "-"),
        )
    
    # =====================================================
    # 5. DETALLES ESPECIFICOS
    # =====================================================
    if tipo == "1":
        # RECLAMO
        pdf.bloque_titulo("5. DETALLES DEL RECLAMO")
        pdf.fila("Materia reclamable", data.get("materia_reclamable", "-"))
        pdf.fila("Problema especifico", data.get("problema_espec", "-"))

        # Campos especificos de materia (si vienen en datos_generales)
        campos_extra = [
            ("N recibo", "numeroReciboFC"), ("Fecha emision", "fechaEmisionFC"),
            ("Fecha vencimiento", "fechaVencimientoFC"), ("Monto recibo", "montoReciboFC"),
            ("Fecha estimada pago", "fechaEstimadaPagoFC"), ("Monto pagado", "montoPagadoFC"),
            ("Monto reclamado", "montoReclamadoFC"), ("Fecha inicio problema", "fechaInicioProblemafs"),
            ("Fecha reactivar servicio", "fechaReactivarServicio"), ("Fecha contratacion", "fechaContratacionServicioInstalacion"),
            ("Fecha solicitud baja", "fechaSolicitudBaja"), ("Fecha emision baja", "fechaEmisionBaja"),
            ("Fecha vencimiento baja", "fechaVencimientoBaja"), ("Fecha solicitud migracion", "fechaSolicitudMigracionX"),
            ("Fecha emision migracion", "fechaEmisionMigracion"), ("Fecha vencimiento migracion", "fechaVencimientoMigracion"),
            ("Descargo del cliente", "descargoReclamo"), ("Informacion necesaria", "informacionNecesariaReclamo"),
        ]
        for label, key in campos_extra:
            val = d.get(key)
            if val:
                pdf.fila(label, str(val))

    elif tipo == "2":
        # QUEJA
        q = data.get("queja", {})
        if q:
            pdf.bloque_titulo("5. DETALLES DE LA QUEJA")
            pdf.fila("Tipo de queja", q.get("idQueja", "-"))
            pdf.fila_doble("Fecha presentacion", q.get("fechaPresentacionQueja", "-"), "Negativa", q.get("negativaQueja", "-"))
            pdf.fila_doble("Fecha negativa", q.get("fechaNegativaQueja", "-"), "Canal", q.get("canalPresentacion", "-"))
            pdf.fila("Especificar canal", q.get("especificarCanalQuejaDos", "-"))
            pdf.fila("Medio probatorio (negativa)", q.get("medioProbatorioNegativa", "-"))
            pdf.fila("Fecha suspension servicio", q.get("fechaSuspendioServicioQueja", "-"))
            pdf.fila("Medios de cobranza", q.get("MediosCobranzasQuejas", "-"))
            pdf.fila("Adjunta prueba", "Si" if q.get("adjuntaPruebaBool") else "No")
            pdf.fila("Constancia de pago", q.get("constanciaPagoMedioCobranza", "-"))
            pdf.fila("Pago a cuenta", q.get("pagoCuentaQueja", "-"))
            pdf.fila("Especificar", q.get("espeficiarQueja", "-"))
            pdf.fila("Captura pruebas", "Si" if q.get("capturaQuejaBool") else "No")
            pdf.fila("Medios probatorios (PG)", q.get("medioProbatoriopgQueja", "-"))
            pdf.fila("Tramitacion", "Si" if q.get("tramitacionBool") else "No")
            pdf.fila("Medios probatorios (tramitacion)", q.get("medioProbatoriosTramitacion", "-"))

    elif tipo == "3":
        # APELACION
        a = data.get("apelacion", {})
        if a:
            pdf.bloque_titulo("5. DATOS DE LA APELACION")

            pdf.bloque_titulo("6. MOTIVOS DE LA APELACION")
            pdf.fila("Motivo especifico 1", a.get("materiaEmpresaEmitirApelacionSeis", "-"))
            pdf.fila("Motivo especifico 2", a.get("materiaEmpresaApelacionTres", "-"))

    # =====================================================
    # 7. ARCHIVOS ADJUNTOS
    # =====================================================
    pdf.bloque_titulo("7. ARCHIVOS ADJUNTOS")
    archivos = data.get("archivos_adjuntos", [])
    if archivos:
        pdf.fila("Archivos recibidos", ", ".join(archivos))
    else:
        pdf.fila("Archivos adjuntos", "No se adjuntaron archivos")

    # =====================================================
    # 8. DESCARGO / SUSTENTO
    # =====================================================
    descargo = d.get("descargoReclamo") or d.get("sustentoApelacion") or ""
    if descargo:
        pdf.bloque_titulo("8. DESCARGO / SUSTENTO DEL CLIENTE")
        pdf.caja("Texto del descargo", str(descargo))

    # =====================================================
    # GUARDAR PDF
    # =====================================================
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name