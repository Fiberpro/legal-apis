from fpdf import FPDF
import tempfile
import os
from zoneinfo import ZoneInfo
from datetime import datetime

ZoneInfo("America/Lima")

# --- LIMPIAR TEXTO ---
def clean_text(txt):
    if not txt:
        return ""
    replacements = {
        "–": "-", "—": "-", "“": '"', "”": '"',
        "‘": "'", "’": "'", "•": "-", "°": "o",
        "…": "...", "©": "(c)", "®": "(R)", "\xa0": " "
    }
    for bad, good in replacements.items():
        txt = txt.replace(bad, good)
    return txt.encode("latin-1", "replace").decode("latin-1").strip()


class PDFReclamoOSIPTEL(FPDF):
    def header(self):
        # ---- LOGO (OSIPTEL) ----
        try:
            self.image("static/osiptel.png", x=10, y=8, w=45)
        except:
            pass

        # ---- FORMULARIO DINÁMICO (RECLAMO / QUEJA / APELACIÓN) ----
        titulo_map = {
            "1": "FORMULARIO DE RECLAMO",
            "2": "FORMULARIO DE QUEJA",
            "3": "FORMULARIO DE RECURSO DE APELACIÓN"
        }

        titulo = titulo_map.get(getattr(self, "tipo_ticket", "3"))

        # ---- TÍTULO PRINCIPAL CENTRADO ----
        self.set_xy(60, 8)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, clean_text(titulo), 0, 1, "L")

        # ---- RECUADRO DE CÓDIGO ----
        self.set_xy(140, 18)
        self.set_font("Arial", "", 10)
        self.cell(65, 8, clean_text("Código de Apelación: _____________"), 1, 1, "C")

        # ---- LÍNEA SEPARADORA ----
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

    # Caja 100% – label arriba, valor abajo
    def caja(self, label, value="", w=190):
        self.set_font("Arial", "B", 10)
        self.cell(w, 6, clean_text(label), 1, 1, "L")  # label ocupa toda la fila
        self.set_font("Arial", "", 10)
        self.multi_cell(w, 8, clean_text(value), 1, "L")  # valor debajo
        self.ln(2)

    # Caja doble 50/50 – todo alineado
    def caja_doble(self, label1, value1, label2, value2):
        # Fila de labels (dos columnas)
        self.set_font("Arial", "B", 10)
        self.cell(95, 6, clean_text(label1), 1, 0, "L")
        self.cell(95, 6, clean_text(label2), 1, 1, "L")

        # Fila de valores
        self.set_font("Arial", "", 10)
        self.cell(95, 8, clean_text(value1), 1, 0, "L")
        self.cell(95, 8, clean_text(value2), 1, 1, "L")
        self.ln(2)

def generar_pdf(data):

    pdf = PDFReclamoOSIPTEL()
    pdf.tipo_ticket = str(data.get("tipo_ticket", "3"))
    pdf.add_page()

    # ===============================
    #  BLOQUE: Datos del Consumidor
    # ===============================
    pdf.titulo_bloque("1. DATOS DEL RECLAMANTE")

    tipo_user_map = {
        "1": "Abonado",
        "2": "Usuario",
        "3": "Representante"
    }

    Departamento="ica"
    Provincia="ica"

    pdf.caja(
        "Condición de quien presenta",
        tipo_user_map.get(str(data.get("tipo_user")), "-")
    )

    pdf.caja_doble(
        "Nombres", data.get("nombrescompletos"),
        "Apellidos", data.get("apellidoscompletos")
    )

    pdf.caja("Razón social", data.get("razonsocial"))

    pdf.caja_doble(
        "Tipo de documento de identidad", data.get("tipodocumento"),
        "Nro de documento de identidad", data.get("numerodocumento")
    )

    # ===============================
    #  BLOQUE: DATOS PARA LA NOTIFICACIÓN Y CONTACTO
    # ===============================
    pdf.titulo_bloque("2. DATOS PARA LA NOTIFICACIÓN Y CONTACTO")

    # Dirección de correo + Autorización
    pdf.caja_doble(
        "Dirección de correo electrónico", data.get("correoelectronico"),
        "Autoriza ser notificado por correo electrónico",
        "Sí" if data.get("autorizacion") else "No"
    )

    # Departamento + Provincia
    pdf.caja_doble(
        "Departamento", data.get("Departamento"),
        "Provincia", data.get("Provincia")
    )

    # Distrito + Dirección
    pdf.caja_doble(
        "Distrito", data.get("distrito"),
        "Dirección", data.get("direccioncasa")
    )

    # Número de teléfono móvil/fijo
    pdf.caja(
        "Numero de teléfono móvil/fijo",
        data.get("movil")
    )

    # ===============================
    # 2. DATOS DE LA APELACIÓN
    # ===============================
    pdf.titulo_bloque("3. DATOS DE LA APELACIÓN")
    pdf.titulo_bloque("DATOS DEL SERVICIO")

    # ===== DATOS DEL SERVICIO =====
    pdf.set_font("Arial", "B", 11)

    # Empresa operadora + Servicio materia apelación
    pdf.caja_doble(
        "Empresa operadora",
        data.get("empresaOperadoraApelacion"),
        "Servicio materia de apelación",
        data.get("servicioMateriaApelacion")
    )

    # Número del servicio reclamado + Especificar otros servicios
    pdf.caja_doble(
        "Número del servicio reclamado o contrato del abonado",
        data.get("numeroServicioContratadoReclamo"),
        "Especificar (Otros servicios)",
        data.get("servicioMateriaReclamo")
    )

    # Código o N° del reclamo + Fecha de emisión de la carta
    pdf.caja_doble(
        "Código o N° de reclamo",
        data.get("codigoNumeroApelacion"),
        "Fecha de emisión de la carta que resuelve el reclamo",
        data.get("fechaEmisionCartaApelacion")
    )

    # ===============================
    # BLOQUE: Motivo de la Apelación
    # ===============================
    pdf.titulo_bloque("4. MOTIVO DE LA APELACIÓN")

    pdf.caja_doble(
        "Motivo específico",
        data.get("materiaEmpresaEmitirApelacionSeis"),
        "", ""  # segunda columna vacía porque en el Excel no tiene segunda parte
    )

    # ===============================
    # 5. MOTIVO DE LA APELACIÓN
    # ===============================
    pdf.titulo_bloque("5. MOTIVO DE LA APELACIÓN")

    pdf.caja_doble(
        "Motivo específico",
        data.get("materiaEmpresaApelacionTres", "-"),
        "", ""
    )


    # ===============================
    # BLOQUE: Archivos Adjuntos (solo texto)
    # ===============================
    pdf.ln(5)
    pdf.titulo_bloque("4. ARCHIVOS ADJUNTOS")

    if data.get("pruebas"):
        pdf.campo("Adjunto", "Sí, contiene archivo(s)")
    else:
        pdf.campo("Adjunto", "No se adjuntaron archivos")

    # ===============================
    # GUARDAR PDF TEMPORAL
    # ===============================
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)

    return temp_file.name
