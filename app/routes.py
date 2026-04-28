from flask import Blueprint, request, session, redirect
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    guardar_usuario,
    registrar_cliente,
    obtener_respuesta,
    guardar_respuesta,
    cargar_respuestas_demo,
    normalizar_numero,
    obtener_respuestas,
    eliminar_respuesta,
    validar_usuario,
    crear_cuenta,
    conectar
)

import os

# 🔒 CLAVE SECRETA PARA SETUP
SETUP_SECRET = os.getenv("SETUP_SECRET", "dev_secret_123")

# 🔥 DEBUG
print("🚀 VERSION NUEVA DEPLOYADA")
print("🔥 ROUTES CARGADO")
print("🔥 ARCHIVO ROUTES REAL:", __file__)
print("🔥 LOGIN + DEBUG DB ACTIVADO")

main = Blueprint('main', __name__)


# 🔥 TEST NUEVO
@main.route("/soy_nuevo")
def soy_nuevo():
    return "🔥 NUEVA RUTA 🔥"


# 🔥 TEST
@main.route("/test")
def test():
    return "🔥 TEST MODIFICADO 🔥"


# 🔹 HOME
@main.route("/")
def home():
    return "CAMBIO REAL NUEVO 999999 🚀"


# 🔥 PING
@main.route("/ping")
def ping():
    print("🔥 PING OK")
    return "pong"


# =========================
# 🔥 SETUP PROTEGIDO
# =========================
@main.route("/setup")
def setup():
    print("🔥 SETUP HIT 🔥")

    # 🔒 PROTECCIÓN POR CLAVE
    secret = request.args.get("key")

    if secret != SETUP_SECRET:
        return "❌ No autorizado", 403

    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            tipo TEXT
        )
        """)

        # 🔥 evitar error si tabla no existe
        try:
            cursor.execute("DELETE FROM respuestas")
        except Exception as e:
            print("⚠️ No se pudo limpiar respuestas:", e)

        cursor.execute("""
            INSERT INTO cuentas (username, password, tipo)
            VALUES (%s, %s, %s)
            ON CONFLICT (username)
            DO UPDATE SET tipo = EXCLUDED.tipo
        """, ("admin", "1234", "14155238886"))

        conn.commit()
        conn.close()

        return "✅ SETUP OK"

    except Exception as e:
        print("❌ ERROR SETUP:", e)
        return f"❌ ERROR: {str(e)}"


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

        Número WhatsApp (ej: 573001234567):<br>
        <input name="numero"><br><br>

        <button type="submit">Registrarse</button>
    </form>
    """


@main.route("/registro", methods=["POST"])
def registro():
    from database import obtener_numero_disponible  # 🔥 IMPORT LOCAL (SEGURO)

    username = request.form.get("username")
    password = request.form.get("password")
    numero_cliente = request.form.get("numero")

    if not username or not password or not numero_cliente:
        return "❌ Faltan datos"

    numero_cliente = normalizar_numero(numero_cliente)

    # 🔥 AQUÍ ESTÁ EL CAMBIO IMPORTANTE
    numero_twilio = obtener_numero_disponible()

    if not numero_twilio:
        return "❌ No hay números disponibles, contacta soporte"

    try:
        # 🔥 ahora guardas ambos correctamente
        crear_cuenta(username, password, numero_twilio, numero_cliente)

        # 🔥 TODAS LAS RESPUESTAS SE GUARDAN CON EL TWILIO (CLAVE)
        guardar_respuesta(numero_twilio, "hola",
            "👋 ¡Hola! Bienvenido\n\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita"
        )
        guardar_respuesta(numero_twilio, "1", "📋 Lista de servicios")
        guardar_respuesta(numero_twilio, "2", "💰 Consulta precios")
        guardar_respuesta(numero_twilio, "3", "📅 Agenda tu cita")

        return f"""
        ✅ Usuario creado correctamente<br><br>

        📱 Tu número de atención es:<br>
        <b>+{numero_twilio}</b><br><br>

        <a href="/login">🔐 Ir a login</a>
        """

    except Exception as e:
        print("❌ ERROR REGISTRO:", e)
        return f"❌ ERROR: {str(e)}"


# =========================
# 🔐 LOGIN
# =========================
@main.route("/login", methods=["GET"])
def login_form():
    return """
    <h2>🔐 Login</h2>
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


# 🔥 LOGOUT
@main.route("/logout")
def logout():
    session.clear()
    return "👋 Sesión cerrada"


# 🔥 PANEL
@main.route("/panel")
def panel():
    if "tipo" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    return f"""
    <h2>🏢 Panel del negocio {tipo}</h2>
    <a href="/respuestas">📋 Ver respuestas</a><br><br>
    <a href="/agregar_form">➕ Agregar respuesta</a><br><br>
    <a href="/logout">🚪 Salir</a>
    """


# 🔥 DEBUG USUARIO
@main.route("/debug_usuario")
def debug_usuario():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT username, tipo FROM cuentas")
    datos = cursor.fetchall()

    conn.close()

    html = "<h2>👀 Usuarios en DB</h2><hr>"

    for user, tipo in datos:
        html += f"{user} → {tipo}<br>"

    return html


# 🔥 WEBHOOK
@main.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 WEBHOOK HIT 🔥")

    try:
        user_number_raw = request.form.get("From", "")
        numero_twilio_raw = request.form.get("To", "")
        incoming_msg_raw = request.form.get("Body", "")

        user_number = normalizar_numero(user_number_raw)
        negocio = normalizar_numero(numero_twilio_raw)
        incoming_msg = incoming_msg_raw.strip().lower()

        if not incoming_msg:
            incoming_msg = "hola"

        registrar_cliente(user_number, negocio)
        guardar_usuario(user_number, incoming_msg, negocio)

        resp = MessagingResponse()
        msg = resp.message()

        respuesta = obtener_respuesta(negocio, incoming_msg)

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


# 🔥 VER RESPUESTAS
@main.route("/respuestas")
def ver_respuestas():
    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]

    datos = obtener_respuestas(numero)

    html = f"<h2>📋 Respuestas de {numero}</h2><hr>"

    for palabra, respuesta in datos:
        html += f"""
        <b>{palabra}</b> → {respuesta}<br>
        <a href="/eliminar?palabra={palabra}">❌ Eliminar</a>
        <hr>
        """

    return html


# 🔥 FORM AGREGAR
@main.route("/agregar_form")
def agregar_form():
    if "tipo" not in session:
        return redirect("/login")

    return """
    <h2>➕ Nueva respuesta</h2>
    <form action="/agregar" method="GET">
        Palabra: <input name="palabra"><br><br>
        Respuesta: <input name="respuesta"><br><br>
        <button type="submit">Guardar</button>
    </form>
    """


# 🔥 AGREGAR
@main.route("/agregar")
def agregar():
    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]
    palabra = request.args.get("palabra")
    respuesta = request.args.get("respuesta")

    if not palabra or not respuesta:
        return "❌ Faltan parámetros"

    guardar_respuesta(numero, palabra, respuesta)

    return "✅ Guardado <br><a href='/panel'>Volver</a>"


# 🔥 ELIMINAR
@main.route("/eliminar")
def eliminar():
    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]
    palabra = request.args.get("palabra")

    if not palabra:
        return "❌ Falta palabra"

    eliminar_respuesta(numero, palabra)

    return "✅ Eliminado <br><a href='/respuestas'>Volver</a>"


print("🔥🔥🔥 FINAL DEL ARCHIVO 🔥🔥🔥")