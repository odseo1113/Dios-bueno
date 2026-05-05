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

print("🚀 VERSION FINAL PRODUCCION")
print("🔥 BOT VENTAS + CITAS ACTIVADO")

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

    guardar_respuesta(numero_twilio, "hola",
        f"👋 Hola, soy el asistente de {username} 🤖\n\n"
        "1️⃣ Servicios\n"
        "2️⃣ Precios\n"
        "3️⃣ Agendar cita\n"
        "4️⃣ Ubicación\n\n"
        "Escribe el número 👇"
    )

    guardar_respuesta(numero_twilio, "1", "📋 Nuestros servicios...")
    guardar_respuesta(numero_twilio, "2", "💰 Nuestros precios...")
    guardar_respuesta(numero_twilio, "4", "📍 Nuestra ubicación...")

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

    <a href="/respuestas">📋 Respuestas</a><br><br>
    <a href="/agregar_form">➕ Agregar respuesta</a><br><br>
    <a href="/citas">📅 Ver citas</a><br><br>

    <a href="/logout">🚪 Salir</a>
    """

# =========================
# 🔥 WEBHOOK (FIX FINAL)
# =========================
@main.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_from = request.form.get("From", "")
        raw_to = request.form.get("To", "")

        user_number = normalizar_numero(raw_from)
        numero_twilio = normalizar_numero(raw_to)

        incoming_msg = (request.form.get("Body", "") or "").strip().lower()

        if not incoming_msg:
            incoming_msg = "hola"

        from database import guardar_cita, obtener_negocio_por_cliente

        # 🔥 FIX CLAVE: fallback robusto
        negocio = obtener_negocio_por_cliente(user_number)
        if not negocio:
            negocio = numero_twilio

        print(f"📩 MSG: {incoming_msg}")
        print(f"👤 FROM(raw): {raw_from} -> {user_number}")
        print(f"🤖 TO(raw): {raw_to} -> {numero_twilio}")
        print(f"🏢 NEGOCIO: {negocio}")

        registrar_cliente(user_number, negocio)
        guardar_usuario(user_number, incoming_msg, negocio)

        resp = MessagingResponse()
        msg = resp.message()

        estado = estado_usuarios.get(user_number)

        # =========================
        # 🔥 CONFIRMAR CITA
        # =========================
        if estado == "esperando_fecha":
            estado_usuarios[user_number] = None

            guardar_cita(user_number, negocio, incoming_msg)

            print(f"📅 NUEVA CITA → {user_number} | {incoming_msg}")

            msg.body(
                f"✅ Cita confirmada 🎉\n\n"
                f"📅 {incoming_msg}\n\n"
                "⏰ Te esperamos"
            )
            return str(resp)

        # =========================
        # 🔥 ACTIVAR CITA
        # =========================
        if incoming_msg == "3" or "cita" in incoming_msg:
            estado_usuarios[user_number] = "esperando_fecha"

            msg.body(
                "📅 Perfecto 👌\n\n"
                "Escribe fecha y hora:\n"
                "Ej: 10 mayo 3pm"
            )
            return str(resp)

        # =========================
        # 🔥 RESPUESTA DB
        # =========================
        respuesta = obtener_respuesta(negocio, incoming_msg)

        if not respuesta:
            print("⚠️ No encontró respuesta exacta")
            respuesta = obtener_respuesta(negocio, "hola")

        if not respuesta:
            print("⚠️ No existe 'hola' en DB")
            respuesta = "👋 Escribe *hola* para comenzar"

        msg.body(respuesta)
        return str(resp)

    except Exception as e:
        print("❌ ERROR WEBHOOK:", str(e))

        resp = MessagingResponse()
        resp.message("Error interno")
        return str(resp)

# =========================
# 🔥 CITAS
# =========================
@main.route("/citas")
def ver_citas():
    if "tipo" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cliente, fecha, estado, creado
        FROM citas
        WHERE negocio = %s
        ORDER BY creado DESC
    """, (tipo,))

    datos = cursor.fetchall()
    conn.close()

    html = f"<h2>📅 Citas de {tipo}</h2><hr>"

    for cliente, fecha, estado, creado in datos:
        html += f"""
        👤 {cliente}<br>
        📅 {fecha}<br>
        📌 {estado}<br>
        🕒 {creado}<br>
        <hr>
        """

    return html

# =========================
# 🔥 RESPUESTAS
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