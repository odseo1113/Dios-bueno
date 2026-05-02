from flask import Blueprint, request, session, redirect
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    guardar_usuario,
    registrar_cliente,
    obtener_respuesta,
    guardar_respuesta,
    normalizar_numero,
    obtener_respuestas,
    eliminar_respuesta,
    validar_usuario,
    crear_cuenta,
    conectar,
    eliminar_cliente
)

import os

SETUP_SECRET = os.getenv("SETUP_SECRET", "dev_secret_123")

print("🚀 VERSION FINAL DEPLOY")
print("🔥 BOT INTELIGENTE + CITAS ACTIVADO")

main = Blueprint('main', __name__)

# =========================
# 🔥 MEMORIA SIMPLE
# =========================
estado_usuarios = {}

# =========================
# 🔹 BASICO
# =========================

@main.route("/")
def home():
    return "BOT OK 🚀"

@main.route("/ping")
def ping():
    return "pong"

# =========================
# 🔥 REGISTRO
# =========================
@main.route("/registro")
def registro_form():
    return """
    <h2>📝 Registro</h2>
    <form action="/registro" method="post">
        Usuario:<br>
        <input name="username"><br><br>

        Contraseña:<br>
        <input name="password" type="password"><br><br>

        Número WhatsApp:<br>
        <input name="numero"><br><br>

        <button type="submit">Registrarse</button>
    </form>
    """

@main.route("/registro", methods=["POST"])
def registro():
    from database import obtener_numero_disponible

    username = request.form.get("username")
    password = request.form.get("password")
    numero_cliente = request.form.get("numero")

    if not username or not password or not numero_cliente:
        return "❌ Faltan datos"

    numero_cliente = normalizar_numero(numero_cliente)
    numero_twilio = obtener_numero_disponible()

    if not numero_twilio:
        return "❌ No hay números disponibles, contacta soporte"

    crear_cuenta(username, password, numero_twilio, numero_cliente)

    # 🔥 MENÚ PRINCIPAL (SIN BLOQUEAR CITAS)
    guardar_respuesta(numero_twilio, "hola",
        f"👋 Hola, soy el asistente de {username} 🤖\n\n"
        "1️⃣ Ver servicios\n"
        "2️⃣ Ver precios\n"
        "3️⃣ Agendar cita\n\n"
        "Escribe el número 👇"
    )

    guardar_respuesta(numero_twilio, "1", "📋 Nuestros servicios disponibles...")
    guardar_respuesta(numero_twilio, "2", "💰 Estos son nuestros precios...")

    return f"""
    ✅ Bot activado 🚀<br><br>
    📲 Escríbele a:<br>
    <b>+{numero_twilio}</b><br><br>
    💡 Escribe "hola"<br><br>
    <a href="/login">Ir al panel</a>
    """

# =========================
# 🔐 LOGIN
# =========================
@main.route("/login", methods=["GET"])
def login_form():
    return """
    <h2>Login</h2>
    <form action="/login" method="POST">
        Usuario: <input name="username"><br><br>
        Password: <input name="password" type="password"><br><br>
        <button type="submit">Entrar</button>
    </form>
    """

@main.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    tipo = validar_usuario(username, password)

    if tipo:
        session["tipo"] = tipo
        return redirect("/panel")

    return "❌ Credenciales incorrectas"

@main.route("/logout")
def logout():
    session.clear()
    return "Sesión cerrada"

# =========================
# 🔥 PANEL
# =========================
@main.route("/panel")
def panel():
    if "tipo" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    return f"""
    <h2>Panel {tipo}</h2>
    <a href="/respuestas">Ver respuestas</a><br><br>
    <a href="/agregar_form">Agregar respuesta</a><br><br>
    <a href="/logout">Salir</a>
    """

# =========================
# 🔥 WEBHOOK INTELIGENTE + CITAS
# =========================
@main.route("/webhook", methods=["POST"])
def webhook():
    try:
        user_number = normalizar_numero(request.form.get("From", ""))
        numero_twilio = normalizar_numero(request.form.get("To", ""))
        incoming_msg = (request.form.get("Body", "") or "").strip().lower()

        if not incoming_msg:
            incoming_msg = "hola"

        from database import obtener_negocio_por_cliente
        negocio = obtener_negocio_por_cliente(user_number) or numero_twilio

        registrar_cliente(user_number, negocio)
        guardar_usuario(user_number, incoming_msg, negocio)

        resp = MessagingResponse()
        msg = resp.message()

        # =========================
        # 🔥 FLUJO DE CITAS
        # =========================
        estado = estado_usuarios.get(user_number)

        if estado == "esperando_fecha":
            estado_usuarios[user_number] = None

            msg.body(
                f"✅ Tu cita quedó agendada:\n\n📅 {incoming_msg}\n\n"
                "Te confirmaremos pronto 🙌"
            )
            return str(resp)

        # =========================
        # 🔥 DETECTOR (ANTES DE DB)
        # =========================
        if incoming_msg == "3" or "cita" in incoming_msg:
            estado_usuarios[user_number] = "esperando_fecha"
            msg.body(
                "📅 Perfecto, vamos a agendar tu cita\n\n"
                "Por favor escribe la fecha y hora 👇\n"
                "Ej: 10 marzo 3pm"
            )
            return str(resp)

        # =========================
        # 🔥 RESPUESTA DESDE DB
        # =========================
        respuesta = (
            obtener_respuesta(negocio, incoming_msg)
            or obtener_respuesta(negocio, "hola")
            or "👋 Escríbenos 'hola' para ver opciones"
        )

        msg.body(respuesta)
        return str(resp)

    except Exception as e:
        print("❌ ERROR WEBHOOK:", e)
        resp = MessagingResponse()
        resp.message("Error interno")
        return str(resp)

# =========================
# 🔥 CRUD RESPUESTAS
# =========================
@main.route("/respuestas")
def ver_respuestas():
    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]
    datos = obtener_respuestas(numero)

    html = "<h2>Respuestas</h2><hr>"

    for palabra, respuesta in datos:
        html += f"{palabra} → {respuesta}<br>"

    return html

@main.route("/agregar_form")
def agregar_form():
    if "tipo" not in session:
        return redirect("/login")

    return """
    <h2>Nueva respuesta</h2>
    <form action="/agregar">
        Palabra: <input name="palabra"><br><br>
        Respuesta: <input name="respuesta"><br><br>
        <button>Guardar</button>
    </form>
    """

@main.route("/agregar")
def agregar():
    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]
    palabra = request.args.get("palabra")
    respuesta = request.args.get("respuesta")

    guardar_respuesta(numero, palabra, respuesta)
    return "Guardado"

@main.route("/eliminar")
def eliminar():
    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]
    palabra = request.args.get("palabra")

    eliminar_respuesta(numero, palabra)
    return "Eliminado"

# =========================
# 🔥 ELIMINAR CLIENTE
# =========================
@main.route("/eliminar_cliente")
def eliminar_cliente_route():
    if "tipo" not in session:
        return redirect("/login")

    username = request.args.get("username")

    ok = eliminar_cliente(username)

    if not ok:
        return "❌ No encontrado"

    return "✅ Eliminado"