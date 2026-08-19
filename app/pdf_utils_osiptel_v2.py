from fpdf import FPDF
import tempfile
from zoneinfo import ZoneInfo
from datetime import datetime

ZoneInfo("America/Lima")

def clean_text(txt):
    if txt is None:
        return ""

    # Convertir todo a string (números, nulls, bools)
    txt = str(txt)

    replacements = {
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "°": "o",
        "…": "...",
        "©": "(c)",
        "®": "(R)",
        "\xa0": " "
    }

    for bad, good in replacements.items():
        txt = txt.replace(bad, good)

    return txt.encode("latin-1", "replace").decode("latin-1").strip()




class PDFReclamoOSIPTEL(FPDF):

    def header(self):
        try:
            self.image("static/osiptel.png", x=10, y=8, w=45)
        except:
            pass

        titulo_map = {
            "1": "FORMULARIO DE RECLAMO",
            "2": "FORMULARIO DE QUEJA",
            "3": "FORMULARIO DE RECURSO DE APELACIÓN"
        }

        titulo = titulo_map.get(getattr(self, "tipo_ticket", "1"))

        # Título
        self.set_xy(60, 8)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, clean_text(titulo), 0, 1, "L")

        # Recuadro código solo en apelación
        if self.tipo_ticket == "3":
            self.set_xy(140, 18)
            self.set_font("Arial", "", 10)
            self.cell(65, 8, clean_text("Código de Apelación: _____________"), 1, 1, "C")

        self.set_xy(10, 28)
        self.set_line_width(0.5)
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, clean_text(f"Generado automáticamente - {fecha}"), align="C")

    def titulo_bloque(self, titulo):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, clean_text(titulo), 0, 1, "L", True)
        self.ln(2)

    def campo(self, label, value):
        self.set_font("Arial", "", 10)
        texto = f"{clean_text(label)}: {clean_text(value) if value else '-'}"
        self.multi_cell(0, 6, texto)
        self.ln(1)

    def caja(self, label, value="", w=190):
        self.set_font("Arial", "B", 10)
        self.cell(w, 6, clean_text(label), 1, 1, "L")
        self.set_font("Arial", "", 10)
        self.multi_cell(w, 8, clean_text(value), 1)
        self.ln(2)

    def caja_doble(self, label1, value1, label2, value2):
        self.set_font("Arial", "B", 10)
        self.cell(95, 6, clean_text(label1), 1, 0, "L")
        self.cell(95, 6, clean_text(label2), 1, 1, "L")

        self.set_font("Arial", "", 10)
        self.cell(95, 8, clean_text(value1), 1, 0, "L")
        self.cell(95, 8, clean_text(value2), 1, 1, "L")
        self.ln(2)


# =====================================================
# 🔵 GENERADOR DEL PDF
# =====================================================
def generar_pdf(data):

    pdf = PDFReclamoOSIPTEL()

    pdf.tipo_ticket = str(data.get("tipo", "1"))
    pdf.add_page()

    # Secciones
    datos = data.get("datos_generales", {})
    queja = data.get("queja", {})
    apelacion = data.get("apelacion", {})

    # =====================================================
    # 1. DATOS DEL RECLAMANTE
    # =====================================================
    pdf.titulo_bloque("1. DATOS DEL RECLAMANTE")

    tipo_user_map = {
        "1": "Abonado",
        "2": "Usuario",
        "3": "Representante"
    }

    pdf.caja("Condición de quien presenta", tipo_user_map.get(str(datos.get("tipo_user")), "-"))

    pdf.caja_doble("Nombres", datos.get("nombrescompletos"),
                   "Apellidos", datos.get("apellidoscompletos"))

    pdf.caja("Razón social", datos.get("razonsocial", ""))

    pdf.caja_doble("Tipo de documento", datos.get("tipodocumento"),
                   "N° documento", datos.get("numerodocumento"))

    # =====================================================
    # 2. CONTACTO
    # =====================================================
    pdf.titulo_bloque("2. DATOS PARA LA NOTIFICACIÓN Y CONTACTO")

    pdf.caja_doble("Correo electrónico", datos.get("correoelectronico"),
                   "Autorización", "Sí" if datos.get("autorizacion") else "No")

    pdf.caja_doble("Distrito", datos.get("distrito"),
                   "Dirección", datos.get("direccioncasa"))

    pdf.caja("Teléfono", datos.get("movil"))

    tipo = str(data.get("tipo"))

    # =====================================================
    # 3. RECLAMO
    # =====================================================
    if tipo == "1":
        pdf.titulo_bloque("3. DETALLES DEL RECLAMO")

        pdf.caja("Materia reclamable", data.get("materiareclamable"))
        pdf.caja("Producto / servicio", data.get("productos"))
        pdf.caja("Monto reclamado", data.get("precio"))
        pdf.caja("Detalle del incumplimiento", data.get("detalle"))
        pdf.caja("Pedido del cliente", data.get("pedido"))

    # =====================================================
    # 4. QUEJA
    # =====================================================
    if tipo == "2":

        q = queja or {}

        pdf.titulo_bloque("3. DETALLES DE LA QUEJA")

        pdf.caja("Tipo de queja", q.get("idQueja"))
        pdf.caja_doble("Fecha presentación", q.get("fechaPresentacionQueja"),
                       "Negativa", q.get("negativaQueja"))

        pdf.caja_doble("Fecha negativa", q.get("fechaNegativaQueja"),
                       "Canal", q.get("canalPresentacion"))

        pdf.caja("Especificar canal", q.get("especificarCanalQuejaDos"))
        pdf.caja("Medio probatorio (negativa)", q.get("medioProbatorioNegativa"))
        pdf.caja("Fecha suspensión servicio", q.get("fechaSuspendioServicioQueja"))
        pdf.caja("Medios de cobranza", q.get("MediosCobranzasQuejas"))
        pdf.caja("Adjunta prueba", "Sí" if q.get("adjuntaPruebaBool") else "No")
        pdf.caja("Constancia de pago", q.get("constanciaPagoMedioCobranza"))
        pdf.caja("Pago a cuenta", q.get("pagoCuentaQueja"))
        pdf.caja("Especificar", q.get("espeficiarQueja"))
        pdf.caja("Captura pruebas", "Sí" if q.get("capturaQuejaBool") else "No")
        pdf.caja("Medios probatorios (PG)", q.get("medioProbatoriopgQueja"))
        pdf.caja("Tramitación", "Sí" if q.get("tramitacionBool") else "No")
        pdf.caja("Medios probatorios (tramitación)", q.get("medioProbatoriosTramitacion"))

    # =====================================================
    # 5. APELACIÓN
    # =====================================================
    if tipo == "3":

        a = apelacion or {}

        pdf.titulo_bloque("3. DATOS DE LA APELACIÓN")
        pdf.titulo_bloque("DATOS DEL SERVICIO")

        pdf.caja_doble("Empresa operadora", a.get("empresaOperadoraApelacion"),
                       "Servicio materia apelación", a.get("servicioMateriaApelacion"))

        pdf.caja_doble("N° servicio reclamado", a.get("numeroServicioContratadoReclamo"),
                       "Otros servicios", a.get("servicioMateriaReclamo"))

        pdf.caja_doble("Código de reclamo", a.get("codigoNumeroApelacion"),
                       "Fecha emisión carta", a.get("fechaEmisionCartaApelacion"))

        pdf.titulo_bloque("4. MOTIVOS DE LA APELACIÓN")

        pdf.caja("Motivo específico 1", a.get("materiaEmpresaEmitirApelacionSeis"))
        pdf.caja("Motivo específico 2", a.get("materiaEmpresaApelacionTres"))

    # =====================================================
    # ADJUNTOS
    # =====================================================
    pdf.titulo_bloque("5. ARCHIVOS ADJUNTOS")

    pdf.campo("Adjunto",
              "Sí, contiene archivo(s)" if data.get("pruebas") else "No se adjuntaron archivos")

    # =====================================================
    # GUARDAR PDF
    # =====================================================
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name