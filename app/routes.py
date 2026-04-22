from flask import Blueprint, request, render_template, send_file, session, redirect
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    guardar_usuario,
    obtener_por_tipo,
    contar_por_tipo,
    validar_usuario,
    obtener_tipo_por_numero,
    registrar_cliente,
    obtener_respuesta,
    obtener_respuestas,
    guardar_respuesta,
    cargar_respuestas_demo,
    eliminar_respuesta
)

import pandas as pd
from io import BytesIO

print("🔥 ROUTES CARGADO")

main = Blueprint('main', __name__)


# 🔥 TEST
@main.route("/test")
def test():
    return "FUNCIONANDO TEST 123"


# 🔹 Home
@main.route("/")
def home():
    return "CAMBIO REAL 999"


# 🔥 CARGAR RESPUESTAS
@main.route("/cargar")
def cargar():
    cargar_respuestas_demo()
    return "✅ Respuestas cargadas"


# 🔐 CREAR ADMIN
@main.route("/crear_admin")
def crear_admin():
    from database import crear_cuenta

    try:
        crear_cuenta("admin", "1234", "abogado")
        return "✅ Usuario creado: admin / 1234"
    except:
        return "⚠️ El usuario ya existe"


# 🔥 SETUP (100% POSTGRES)
@main.route("/setup")
def setup():
    from database import conectar

    try:
        conn = conectar()
        cursor = conn.cursor()

        # 🔥 LIMPIAR
        cursor.execute("DELETE FROM respuestas")

        # 🔐 USUARIOS
        cursor.execute(
            "INSERT INTO cuentas (username, password, tipo) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ("admin", "1234", "abogado")
        )
        cursor.execute(
            "INSERT INTO cuentas (username, password, tipo) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ("peluqueria", "1234", "peluqueria")
        )
        cursor.execute(
            "INSERT INTO cuentas (username, password, tipo) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ("canina", "1234", "peluqueria_canina")
        )

        # ⚖️ ABOGADO
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("abogado", "hola", "⚖️ Bienvenido\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("abogado", "1", "⚖️ Derecho laboral, civil, familiar"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("abogado", "2", "💰 Desde $50.000"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("abogado", "3", "📅 Agenda tu cita"))

        # 💇 PELUQUERIA
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria", "hola", "💇 Bienvenido\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria", "1", "✂️ Corte, peinado, tintes"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria", "2", "💰 Desde $20.000"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria", "3", "📅 Agenda tu cita"))

        # 🐶 CANINA
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria_canina", "hola", "🐶 Peluquería canina\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria_canina", "1", "🛁 Baño, corte y limpieza"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria_canina", "2", "💰 Desde $30.000"))
        cursor.execute("INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)", ("peluqueria_canina", "3", "📅 Agenda para tu mascota"))

        conn.commit()
        conn.close()

        return "✅ SETUP OK"

    except Exception as e:
        return f"❌ ERROR REAL: {str(e)}"


# 🔹 WEBHOOK
@main.route("/webhook", methods=["POST"])
def webhook():
    user_number = request.form.get("From", "")
    incoming_msg = request.form.get("Body", "").strip().lower()

    if incoming_msg.startswith("test1"):
        tipo_cliente = "peluqueria"

    elif incoming_msg.startswith("test2"):
        tipo_cliente = "peluqueria_canina"

    else:
        tipo_cliente = obtener_tipo_por_numero(user_number)

        if not tipo_cliente:
            registrar_cliente(user_number, "abogado")
            tipo_cliente = "abogado"

    incoming_msg = incoming_msg.replace("test1", "").replace("test2", "").strip()

    guardar_usuario(user_number, incoming_msg, tipo_cliente)

    resp = MessagingResponse()
    msg = resp.message()

    respuesta = obtener_respuesta(tipo_cliente, incoming_msg)

    if respuesta:
        msg.body(respuesta)
    else:
        msg.body("Escribe 'hola'")

    return str(resp)