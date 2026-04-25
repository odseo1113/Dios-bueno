from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    guardar_usuario,
    registrar_cliente,
    obtener_respuesta,
    guardar_respuesta,
    cargar_respuestas_demo,
    normalizar_numero,
    obtener_respuestas,
    eliminar_respuesta
)

# 🔥 DEBUG
print("🚀 VERSION NUEVA DEPLOYADA")
print("🔥 ROUTES CARGADO")
print("🔥 ARCHIVO ROUTES REAL:", __file__)  # 👈 ESTA LÍNEA NUEVA

main = Blueprint('main', __name__)


# 🔥 TEST
@main.route("/test")
def test():
    return "FUNCIONANDO TEST 123"


# 🔹 HOME
@main.route("/")
def home():
    return "CAMBIO REAL NUEVO 999999 🚀"


# 🔥 PING
@main.route("/ping")
def ping():
    print("🔥 PING OK")
    return "pong"


# 🔥 CARGAR RESPUESTAS
@main.route("/cargar")
def cargar():
    cargar_respuestas_demo()
    return "✅ Respuestas cargadas"


# 🔥 SETUP
@main.route("/setup")
def setup():
    from database import conectar

    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM respuestas")

        cursor.execute(
            """
            INSERT INTO cuentas (username, password, tipo)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            """,
            ("admin", "1234", "abogado")
        )

        conn.commit()
        conn.close()

        return "✅ SETUP OK"

    except Exception as e:
        print("❌ ERROR SETUP:", e)
        return f"❌ ERROR: {str(e)}"


# 🔥 RESET CLIENTES
@main.route("/reset_clientes")
def reset_clientes():
    from database import conectar

    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM clientes")

        conn.commit()
        conn.close()

        return "✅ clientes reseteados"

    except Exception as e:
        print("❌ ERROR RESET:", e)
        return f"❌ ERROR: {str(e)}"


# 🔥 SETUP CLIENTE
@main.route("/setup_cliente", methods=["GET"], strict_slashes=False)
def setup_cliente():
    print("🔥🔥🔥 SETUP_CLIENTE HIT 🔥🔥🔥")

    from database import conectar

    numero = request.args.get("numero")

    if not numero:
        return "❌ Falta parámetro numero"

    numero = normalizar_numero(numero)
    print("📌 NUMERO CONFIG:", numero)

    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM respuestas WHERE tipo = %s",
            (numero,)
        )

        conn.commit()
        conn.close()

        guardar_respuesta(numero, "hola",
            "🐶 ¡Hola! Bienvenido a *Peluquería Canina 🐾*\n\n"
            "1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita\n4️⃣ Ubicación"
        )

        guardar_respuesta(numero, "1", "🛁 Baño, corte, limpieza")
        guardar_respuesta(numero, "2", "💰 Desde $30.000")
        guardar_respuesta(numero, "3", "📅 Agenda tu cita")
        guardar_respuesta(numero, "4", "📍 Dirección aquí")

        return f"✅ Cliente {numero} configurado"

    except Exception as e:
        print("❌ ERROR SETUP_CLIENTE:", e)
        return f"❌ ERROR: {str(e)}"


# 🔥 PANEL VER RESPUESTAS
@main.route("/respuestas")
def ver_respuestas():
    numero = request.args.get("numero")

    if not numero:
        return "❌ Falta parámetro numero"

    numero = normalizar_numero(numero)

    datos = obtener_respuestas(numero)

    html = f"<h2>📋 Respuestas de {numero}</h2><hr>"

    for palabra, respuesta in datos:
        html += f"""
        <b>{palabra}</b> → {respuesta}<br>
        <a href="/eliminar?numero={numero}&palabra={palabra}">❌ Eliminar</a>
        <hr>
        """

    return html


# 🔥 AGREGAR RESPUESTA
@main.route("/agregar")
def agregar():
    numero = request.args.get("numero")
    palabra = request.args.get("palabra")
    respuesta = request.args.get("respuesta")

    if not numero or not palabra or not respuesta:
        return "❌ Faltan parámetros"

    numero = normalizar_numero(numero)

    guardar_respuesta(numero, palabra, respuesta)

    return "✅ Guardado"


# 🔥 ELIMINAR RESPUESTA
@main.route("/eliminar")
def eliminar():
    numero = request.args.get("numero")
    palabra = request.args.get("palabra")

    if not numero or not palabra:
        return "❌ Faltan parámetros"

    eliminar_respuesta(numero, palabra)

    return "✅ Eliminado"


# 🔥 WEBHOOK
@main.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 WEBHOOK HIT 🔥")

    try:
        user_number_raw = request.form.get("From", "")
        numero_twilio_raw = request.form.get("To", "")
        incoming_msg = request.form.get("Body", "").strip().lower()

        user_number = normalizar_numero(user_number_raw)
        negocio = normalizar_numero(numero_twilio_raw)

        print("📌 NEGOCIO:", negocio)
        print("👤 USUARIO:", user_number)
        print("💬 MENSAJE:", incoming_msg)

        registrar_cliente(user_number, negocio)
        guardar_usuario(user_number, incoming_msg, negocio)

        resp = MessagingResponse()
        msg = resp.message()

        # 🔥 RESPUESTA + FALLBACK
        respuesta = obtener_respuesta(negocio, incoming_msg)

        print("🧠 RESPUESTA DB:", respuesta)

        if not respuesta:
            respuesta = obtener_respuesta(negocio, "hola")

        if not respuesta:
            respuesta = "🐶 Escribe 'hola' para comenzar"

        msg.body(respuesta)

        return str(resp)

    except Exception as e:
        print("❌ ERROR WEBHOOK:", e)
        resp = MessagingResponse()
        resp.message("Error interno")
        return str(resp)