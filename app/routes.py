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
    eliminar_cliente,
    guardar_estado,
    obtener_estado
)

import os

SETUP_SECRET = os.getenv("SETUP_SECRET", "dev_secret_123")

print("🚀 VERSION FINAL PRODUCCION")
print("🔥 BOT VENTAS + CITAS ACTIVADO")

main = Blueprint('main', __name__)


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
# 🔥 PANEL PROFESIONAL
# =========================
@main.route("/panel")
def panel():
    if "tipo" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    conn = conectar()
    cursor = conn.cursor()

    # =========================
    # 🔥 TOTAL MENSAJES
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM usuarios
        WHERE tipo = %s
    """, (tipo,))

    total_mensajes = cursor.fetchone()[0]

    # =========================
    # 🔥 TOTAL CLIENTES
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM clientes
        WHERE tipo = %s
    """, (tipo,))

    total_clientes = cursor.fetchone()[0]

    # =========================
    # 🔥 TOTAL CITAS
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM citas
        WHERE negocio = %s
    """, (tipo,))

    total_citas = cursor.fetchone()[0]

    conn.close()

    return f"""
    <html>
    <head>
        <title>Panel SaaS</title>

        <style>
            body {{
                background: #f5f7fb;
                font-family: Arial;
                padding: 30px;
            }}

            .top {{
                margin-bottom: 30px;
            }}

            .card-container {{
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                margin-bottom: 30px;
            }}

            .card {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                min-width: 220px;
            }}

            .card h3 {{
                margin: 0;
                color: #666;
            }}

            .number {{
                font-size: 35px;
                font-weight: bold;
                margin-top: 10px;
                color: #111;
            }}

            .menu {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }}

            .menu a {{
                display: block;
                padding: 15px;
                margin-bottom: 10px;
                background: #0d6efd;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }}

            .menu a:hover {{
                background: #0b5ed7;
            }}

            .logout {{
                background: #dc3545 !important;
            }}

            .logout:hover {{
                background: #bb2d3b !important;
            }}
        </style>
    </head>

    <body>

        <div class="top">
            <h1>🤖 Panel SaaS WhatsApp</h1>
            <p><b>Negocio:</b> {tipo}</p>
        </div>

        <div class="card-container">

            <div class="card">
                <h3>💬 Mensajes</h3>
                <div class="number">{total_mensajes}</div>
            </div>

            <div class="card">
                <h3>👥 Clientes</h3>
                <div class="number">{total_clientes}</div>
            </div>

            <div class="card">
                <h3>📅 Citas</h3>
                <div class="number">{total_citas}</div>
            </div>

        </div>

        <div class="menu">

            <a href="/respuestas">
                📋 Ver respuestas
            </a>

            <a href="/agregar_form">
                ➕ Agregar respuesta
            </a>

            <a href="/citas">
                📅 Ver citas
            </a>

            <a href="/logout" class="logout">
                🚪 Cerrar sesión
            </a>

        </div>

    </body>
    </html>
    """

# =========================
# 🔥 WEBHOOK (PRODUCCION FINAL OK + PERSISTENCIA)
# =========================
@main.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_from = request.form.get("From", "")
        raw_to = request.form.get("To", "")
        raw_body = request.form.get("Body", "")

        user_number = normalizar_numero(raw_from)
        numero_twilio = normalizar_numero(raw_to)

        incoming_msg = (raw_body or "").strip()

        if not incoming_msg:
            incoming_msg = "hola"

        incoming_msg = incoming_msg.lower()

        print("🔥 WEBHOOK HIT")
        print(f"📩 MSG: {incoming_msg}")
        print(f"👤 FROM(raw): {raw_from} -> {user_number}")
        print(f"🤖 TO(raw): {raw_to} -> {numero_twilio}")

        from database import guardar_cita, obtener_negocio_por_cliente

        # =========================
        # 🔥 OBTENER NEGOCIO
        # =========================
        negocio = obtener_negocio_por_cliente(user_number)

        if not negocio:
            negocio = numero_twilio

        print(f"🏢 NEGOCIO: {negocio}")
        print(f"🔥 TIPO USADO WEBHOOK: {negocio}")

        # =========================
        # 🔥 GUARDAR DATOS
        # =========================
        registrar_cliente(user_number, negocio)
        guardar_usuario(user_number, incoming_msg, negocio)

        resp = MessagingResponse()
        msg = resp.message()

        # =========================
        # 🔥 ESTADO DESDE DB
        # =========================
        estado = obtener_estado(user_number)

        # =========================
        # 🔥 CONFIRMAR CITA
        # =========================
        if estado == "esperando_fecha":

            guardar_estado(user_number, "")

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

            guardar_estado(user_number, "esperando_fecha")

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

        print(f"🔎 RESPUESTA EXACTA: {respuesta}")

        if not respuesta:
            print("⚠️ No encontró respuesta exacta")
            respuesta = obtener_respuesta(negocio, "hola")

        print(f"🔎 RESPUESTA FALLBACK: {respuesta}")

        if not respuesta:
            print("⚠️ No existe 'hola' en DB")
            respuesta = "👋 Hola, el bot está activo"

        msg.body(respuesta)

        print("✅ RESPUESTA ENVIADA")

        return str(resp)

    except Exception as e:
        print("❌ ERROR WEBHOOK:", str(e))

        resp = MessagingResponse()
        resp.message("❌ Error interno")

        return str(resp)