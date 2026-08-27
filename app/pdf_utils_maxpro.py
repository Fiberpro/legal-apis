from fpdf import FPDF
from datetime import datetime
from zoneinfo import ZoneInfo
import os, tempfile

ZoneInfo("America/Lima")

# --- LIMPIAR TEXTO ---
def clean_text(txt):
    if not txt:
        return ""
    txt = str(txt)
    replacements = {
        "–": "-", "—": "-", "“": '"', "”": '"',
        "‘": "'", "’": "'", "•": "-", "°": "o",
        "…": "...", "©": "(c)", "®": "(R)", "\xa0": " ",
        "ñ": "n", "Ñ": "N", "á": "a", "é": "e", "í": "i",
        "ó": "o", "ú": "u", "Á": "A", "É": "E", "Í": "I",
        "Ó": "O", "Ú": "U", "ü": "u", "Ü": "U"
    }
    for bad, good in replacements.items():
        txt = txt.replace(bad, good)
    # evita errores con Helvetica
    return txt.encode("latin-1", "replace").decode("latin-1").strip()

# MAPEO DE PROVINCIA
# --- MAPEOS DE PROVINCIA ---
def map_provincia(value):
    try:
        i = int(value)
    except (ValueError, TypeError):
        return value or ""
    mapping = {
        128: "Lima",
        134: "Huarochirí",
        67: "Callao",
        100: "Chincha",
        103: "Pisco",
    }
    return mapping.get(i, str(value))

# --- MAPEOS DE DISTRITO ---
def map_distrito(value, provincia_id=None):
    try:
        i = int(value)
    except (ValueError, TypeError):
        return value or ""

    distritos_lima = {
        1282: "Ancón",
        1283: "Ate",
        1286: "Carabayllo",
        1891: "Cercado de Lima",
        1287: "Chaclacayo",
        1290: "Comas",
        1291: "El Agustíno",
        1292: "Independencia",
        1295: "La Victoria",
        1297: "Los Olivos",
        1876: "Lurigancho-Chosica",
        1305: "Puente Piedra",
        1308: "Rímac",
        1911: "San Juan de Lurigancho",
        1315: "San Martín de Porres",
        1317: "Santa Anita",
        1319: "Santa Rosa",
    }

    distritos_callao = {
        690: "Callao",
        692: "Carmen de la Legua Reynoso",
        693: "La Perla",
        695: "Ventanilla",
        696: "Mi Perú",
    }

    distritos_huarochiri = {
        1502: "San Antonio",
        1875: "San Antonio de Chaclla",
    }
    
    distritos_chincha = {
        1007: "Chincha Alta",
        1008: "Alta Laram",
        1010: "Chincha Baja",
        1011: "El Carmen",
        1012: "Grocio Prado",
        1013: "Pueblo Nuevo",
        1016: "Sunampe",
        1017: "Tambo de Mora",
    }
    
    distritos_pisco = {
        1028: "Pisco",
        1030: "Humay",
        1031: "Chincha Baja",
        1034: "San Clemente",
        1035: "Tupac Amaru Inca",
    }

    # Seleccionar mapeo según provincia
    if provincia_id in ("128", 128):
        return distritos_lima.get(i, str(value))
    elif provincia_id in ("67", 67):
        return distritos_callao.get(i, str(value))
    elif provincia_id in ("134", 134):
        return distritos_huarochiri.get(i, str(value))
    elif provincia_id in ("100", 100):
        return distritos_chincha.get(i, str(value))
    elif provincia_id in ("103", 103):
        return distritos_pisco.get(i, str(value))
    else:
        return str(value)

# --- MAPEOS DE MATERIA ---
def map_materia(value):
    if not value:
        return ""
    try:
        i = int(value)
    except (ValueError, TypeError):
        return str(value)
    mapping = {
        1: "Problemas con mi router/modem",
        2: "Problemas con mi repetidor",
        3: "Otros",
        4: "Problema con atención presencial",
        5: "Problema con atención por WhatsApp",
        6: "Problema con atención telefónica",
        7: "Problemas con la instalación",
        8: "Problemas durante la visita técnica",
    }
    return mapping.get(i, f"Opción {i}")

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        # 🧩 Asegura fuente configurada ANTES de escribir
        self.set_font("helvetica", "B", 16)

        self.set_fill_color(232, 60, 103)
        self.rect(0, 0, 210, 30, "F")
        logo_path = "./static/Logo-maxpro.png"
        if os.path.exists(logo_path):
            self.image(logo_path, 5, 5, 45)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "LIBRO DE RECLAMACIONES", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

# --- FUNCIÓN PRINCIPAL ---
def generar_pdf(data):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # 🧩 Asegura fuente global
    pdf.set_font("helvetica", "", 11)

    # --- SEDE ---
    sedesicalima = str(data.get("sedesicalima", "")).strip()
    direccion_sede = "-"
    provincia = data.get("provincias", "")
    distrito = data.get("distrito", "")

    sedesicalima = str(data.get("sedesicalima", "")).strip()
    if sedesicalima == "1":
        pdf.set_font("helvetica", "B", 10)
        direccion_sede = "Av. L Mza. L Lote 48, Carabayllo, Lima"
    elif sedesicalima == "2":
        pdf.set_font("helvetica", "B", 10)
        direccion_sede = "Otr. Yaurilla Mza. T2 Lote 10, C.P. Yaurilla, Los Aquijes, Ica"
    elif sedesicalima == "3":
        pdf.set_font("helvetica", "B", 10)
        direccion_sede = "Upis Mz R Lt 13 A.H. El Carmen, EL Carmen, Chincha"
    else:
        nombre_sede = "Sede desconocida"
        direccion_sede = "-"

    provincia = map_provincia(provincia)
    distrito = map_distrito(distrito, data.get("provincias"))

    # --- INFORMACIÓN DE LA EMPRESA ---
    pdf.set_font("helvetica", "", 10)
    pdf.ln(6)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(130, 6, "Corporación Luan Pro S.a.C. - RUC: 20612863548", ln=0)
    pdf.set_font("helvetica", "B", 10)
    lima_now = datetime.now(ZoneInfo("America/Lima"))
    pdf.cell(0, 6, f"Fecha: {lima_now.strftime('%d/%m/%Y')}", align="R", ln=1)

    # 👉 Dirección y código en la misma línea
    if sedesicalima == "1" and data.get("ticket_number"):
        pdf.cell(130, 6, f" {direccion_sede}", ln=0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, f"Código: {data['ticket_number']}", align="R", ln=1)
        pdf.set_font("helvetica", "", 11)
    elif sedesicalima == "3" and data.get("ticket_number"):
        pdf.cell(130, 6, f" {direccion_sede}", ln=0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, f"Código: {data['ticket_number']}", align="R", ln=1)
        pdf.set_font("helvetica", "", 11)
    else:
        pdf.cell(0, 6, f"{direccion_sede}", ln=1)
        if data.get("ticket_number"):
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, f"Código: {data['ticket_number']}", align="R", ln=1)

    pdf.ln(6)

    # 1️⃣ IDENTIFICACIÓN DEL CONSUMIDOR
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "1. IDENTIFICACIÓN DEL CONSUMIDOR", ln=True)
    pdf.set_font("helvetica", "", 11)

    campos = [
        ("Nombres y apellidos", f"{data.get('nombrescompletos','')} {data.get('apellidoscompletos','')}"),
        ("Domicilio", data.get("direccioncasa","")),
        ("Departamento / Provincia / Distrito",
        f"{data.get('departamento','')} / {provincia} / {distrito}"),
        ("Documento", f"{data.get('tipodocumento','')} - {data.get('numerodocumento','')}"),
        ("Correo", data.get("correoelectronico","")),
        ("Celular", data.get("movil","")),
        ("Menor de edad", data.get("menorEdad","")),
    ]
    for campo, valor in campos:
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 6, f"{campo}:", ln=True)
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 6, clean_text(valor))
        pdf.ln(2)

    # 2️⃣ BIEN ADQUIRIDO
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "2. IDENTIFICACIÓN DEL BIEN ADQUIRIDO", ln=True)
    pdf.set_font("helvetica", "", 11)
    detalle = [
        ("Tipo de bien", map_materia(data.get("materiareclamable",""))),
        ("Monto del producto o servicio", data.get("precio","")),
        ("Descripción", data.get("detalle","")),
    ]
    for campo, valor in detalle:
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 6, f"{campo}:", ln=True)
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 6, clean_text(valor))
        pdf.ln(2)

    # 3️⃣ RECLAMACIÓN
    pdf.add_page()
    pdf.set_y(40)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 10, "3. TIPO Y DETALLE DE LA RECLAMACIÓN", ln=True)
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(90, 10, "Tipo de Reclamación", 1, 0, "C")
    pdf.cell(50, 10, "Reclamo", 1, 0, "C")
    pdf.cell(50, 10, "Queja", 1, 1, "C")
    pdf.cell(90, 10, "", 1, 0, "C")
    pdf.cell(50, 10, "X" if data.get("tipo") == "1" else "", 1, 0, "C")
    pdf.cell(50, 10, "X" if data.get("tipo") == "2" else "", 1, 1, "C")
    pdf.cell(190, 10, "Detalle de la Reclamación", 1, 1, "C")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(190, 8, clean_text(data.get("detalle", "")), 1, "L")
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 10, "Pedido concreto del consumidor", 1, 1, "C")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(190, 8, clean_text(data.get("pedido", "")), 1, "L")

    # --- SECCIÓN 4 ---
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "4. OBSERVACIONES Y ACCIONES ADOPTADAS", ln=True)

    pdf.set_font("helvetica", "", 11)

    # --- Tabla superior con Reclamo / Queja ---
    pdf.cell(95, 10, "Reclamo:", 1, 0, "L")
    pdf.cell(95, 10, "Queja:", 1, 1, "L")

    # --- Espacio vacío debajo de la tabla ---
    pdf.cell(95, 20, "", 1, 0, "L")
    pdf.cell(95, 20, "", 1, 1, "L")

    # --- Firmas ---
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 10, "FIRMA DEL CONSUMIDOR", 1, 0, "C")
    pdf.cell(95, 10, "FIRMA DEL PROVEEDOR", 1, 1, "C")

    pdf.ln(6)

    # PIE
    pdf.ln(10)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, clean_text(
        "*El proveedor deberá dar respuesta al reclamo en un plazo no mayor a quince (15) días hábiles improrrogable.\n\n"
        "*Esta cuenta de correo se utiliza exclusivamente para el envío de constancias de recepción de reclamos. No está habilitada para recibir mensajes. Por favor, sírvase de no enviar correos a esta dirección electrónica."
    ))
    # 🔹 Guardar PDF de forma controlada y temporal
    ticket_number = data.get("ticket_number", f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    pdf_path = f"./static/temp/{ticket_number}.pdf"

    # Crear carpeta si no existe
    os.makedirs("./static/temp", exist_ok=True)

    pdf.output(pdf_path)
    return pdf_path