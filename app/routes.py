from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    guardar_usuario,
    registrar_cliente,
    obtener_respuesta,
    guardar_respuesta,
    cargar_respuestas_demo,
    normalizar_numero
)

# 🔥 DEBUG
print("🚀 VERSION NUEVA DEPLOYADA")
print("🔥 ROUTES CARGADO")

main = Blueprint('main', __name__)


# 🔥 TEST
@main.route("/test")
def test():
    return "FUNCIONANDO TEST 123"


# 🔹 HOME
@main.route("/")
def home():
    return "CAMBIO REAL NUEVO 999999 🚀"


# 🔥 PING (PRUEBA CLAVE)
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


# 🔥 SETUP CLIENTE (FIX REAL)
@main.route("/setup_cliente", methods=["GET"], strict_slashes=False)
def setup_cliente():
    print("🔥🔥🔥 SETUP_CLIENTE HIT 🔥🔥🔥")

    from database import conectar, guardar_respuesta

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

        # 🔥 RESPUESTAS
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


# 🔥 WEBHOOK
@main.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 WEBHOOK HIT 🔥")

    try:
        user_number = request.form.get("From", "")
        numero_twilio = request.form.get("To", "")
        incoming_msg = request.form.get("Body", "").strip().lower()

        negocio = normalizar_numero(numero_twilio)

        print("NEGOCIO:", negocio)
        print("USUARIO:", user_number)
        print("MENSAJE:", incoming_msg)

        registrar_cliente(user_number, negocio)
        guardar_usuario(user_number, incoming_msg, negocio)

        resp = MessagingResponse()
        msg = resp.message()

        respuesta = obtener_respuesta(negocio, incoming_msg)

        if respuesta:
            msg.body(respuesta)
        else:
            msg.body("🐶 Escribe 'hola'")

        return str(resp)

    except Exception as e:
        print("❌ ERROR WEBHOOK:", e)
        resp = MessagingResponse()
        resp.message("Error interno")
        return str(resp)