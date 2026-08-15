# main.py
import os
from fastapi import FastAPI, HTTPException, Body, status
from fastapi.middleware.cors import CORSMiddleware
from app.pdf_utils import generar_pdf
from app.services import settings, odoo, enviar_correo_con_pdf

app = FastAPI(title="API Libro de Reclamaciones - FiberPro", version="2.0.0")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1️⃣ LIBRO DE RECLAMACIONES - ICA
@app.post("/api/enviar_pdf")
def api_enviar_pdf(data: dict = Body(...)):
    pdf_path = None
    try:
        pdf_path = generar_pdf(data)
        correo_destino = settings.MAIL_RECEPTOR

        cuerpo = (
            f"Estimado/a el cliente {data.get('nombrescompletos','')} "
            f"{data.get('apellidoscompletos','')} presenta un reclamo/queja de indecopi,\n\n"
        )

        enviar_correo_con_pdf(
            destinatario=correo_destino,
            asunto="Libro de Reclamaciones INDECOPI - FiberPro-ICA",
            cuerpo=cuerpo,
            ruta_pdf=pdf_path
        )

        return {
            "success": True,
            "message": f"📄 PDF enviado correctamente a {correo_destino}"
        }

    except Exception as e:
        print("❌ Error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)


# 2️⃣ LIBRO DE RECLAMACIONES - LIMA / ODOO
@app.post("/api/libroreclamaciones/v2")
def crear_libro_reclamacionesv2(data: dict = Body(...)):
    sedesicalima = str(data.get('sedesicalima', '')).strip()
    correo = data.get("correoelectronico")

    # --- Validaciones ---
    if sedesicalima != "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se registran reclamos de Lima en Odoo."
        )

    required_fields = [
        'tipo', 'tipodocumento', 'numerodocumento',
        'nombrescompletos', 'apellidoscompletos',
        'materiareclamable', 'detalle', 'pedido'
    ]
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Falta el campo requerido: {field}"
            )

    # --- 1. Crear registro en Odoo ---
    try:
        ticket_libro = {
            'tipo': int(data.get('tipo')),
            'tipo_identificacion': data.get('tipodocumento'),
            'nif': data.get('numerodocumento'),
            'nombres': data.get('nombrescompletos'),
            'apellidos': data.get('apellidoscompletos'),
            'departamento': data.get('departamento'),
            'provincias': data.get('provincias'),
            'distrito': data.get('distrito'),
            'correo': correo,
            'movil': data.get('movil'),
            'direccion': data.get('direccioncasa'),
            'autorizacion': data.get('autorizacion'),
            'nombreapoderado': data.get('nombrePadre'),
            'materia_reclamo': data.get('materiareclamable'),
            'especifique_reclamo': data.get('otrosreclamable'),
            'identificion_producto_reclamo': data.get('productos'),
            'monto_producto_reclamo': data.get('precio'),
            'especifique_incoveniente': data.get('detalle'),
            'pedido_concreto_consumidor': data.get('pedido'),
        }

        ticket_id = odoo.execute_kw(
            model='indecopi.complaints',
            method='create',
            args=[ticket_libro]
        )

        ticket_data = odoo.execute_kw(
            model='indecopi.complaints',
            method='read',
            args=[ticket_id],
            kwargs={'fields': ['name']}
        )
        ticket_number = ticket_data[0]['name']
        print(f"✅ Ticket creado en Odoo: {ticket_number}")

    except Exception as e:
        print("❌ Error al crear en Odoo:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear ticket en Odoo: {str(e)}"
        )

    # --- 2. Generar PDF y Enviar Correo ---
    pdf_path = None
    try:
        data["ticket_number"] = ticket_number
        pdf_path = generar_pdf(data)
        print("📄 PDF generado:", pdf_path)

        cuerpo = (
            f"Hola {data.get('nombrescompletos','')}, 👋\n\n"
            f"Tu reclamo ha sido recibido correctamente y se ha generado el número: {ticket_number}\n\n"
            f"Hemos adjuntado una copia del reclamo en formato PDF.\n\n"
            f"Gracias por contactarte con FiberPro.\n\n"
            f"Atentamente,\nEquipo FiberPro"
        )

        enviar_correo_con_pdf(
            destinatario=correo,
            asunto="Libro de Reclamaciones INDECOPI - FiberPro - Lima",
            cuerpo=cuerpo,
            ruta_pdf=pdf_path
        )
        print(f"📧 Correo con PDF enviado a {correo}")

    except Exception as e:
        print("⚠️ Error generando PDF o enviando correo:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando correo con PDF: {str(e)}"
        )
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)

    # --- 3. Respuesta final ---
    return {
        "success": True,
        "ticket_id": ticket_number,
        "message": (
            f"Reclamo registrado correctamente. "
            f"Se envió una copia del PDF al correo {correo}."
        )
    }