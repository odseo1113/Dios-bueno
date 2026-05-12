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

        <button type="submit">
            Registrarse
        </button>

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
        return "❌ No hay números disponibles"

    crear_cuenta(
        username,
        password,
        numero_twilio,
        numero_cliente
    )

    # =========================
    # 🔥 RESPUESTAS DEFAULT
    # =========================

    guardar_respuesta(
        numero_twilio,
        "hola",
        f"👋 Hola, somos {username} 🤖\n\n"
        "🔥 Tenemos disponibilidad HOY\n\n"
        "1️⃣ Servicios\n"
        "2️⃣ Precios\n"
        "3️⃣ Agendar cita\n"
        "4️⃣ Ubicación\n\n"
        "Responde con el número 👇"
    )

    guardar_respuesta(
        numero_twilio,
        "1",
        "📋 Nuestros servicios disponibles"
    )

    guardar_respuesta(
        numero_twilio,
        "2",
        "💰 Consulta nuestros precios"
    )

    guardar_respuesta(
        numero_twilio,
        "4",
        "📍 Estamos disponibles hoy"
    )

    return f"""
    <h2>✅ BOT ACTIVADO</h2>

    <b>Tu número asignado:</b><br><br>

    +{numero_twilio}<br><br>

    <a href="/login">
        Ir al panel
    </a>
    """

# =========================
# 🔐 LOGIN
# =========================
@main.route("/login", methods=["GET"])
def login_form():
    return """
    <h2>🔐 Login</h2>

    <form action="/login" method="POST">

        Usuario:<br>
        <input name="username"><br><br>

        Password:<br>
        <input name="password" type="password"><br><br>

        <button type="submit">
            Entrar
        </button>

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
    return redirect("/login")

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
    # 🔥 MENSAJES
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM usuarios
        WHERE tipo = %s
    """, (tipo,))

    total_mensajes = cursor.fetchone()[0]

    # =========================
    # 🔥 CLIENTES
    # =========================
    cursor.execute("""
        SELECT COUNT(*)
        FROM clientes
        WHERE tipo = %s
    """, (tipo,))

    total_clientes = cursor.fetchone()[0]

    # =========================
    # 🔥 CITAS
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

            .number {{
                font-size: 35px;
                font-weight: bold;
                margin-top: 10px;
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

            .logout {{
                background: #dc3545 !important;
            }}

        </style>

    </head>

    <body>

        <h1>🤖 Panel SaaS WhatsApp</h1>

        <p>
            <b>Negocio:</b> {tipo}
        </p>

        <div class="card-container">

            <div class="card">
                <h3>💬 Mensajes</h3>
                <div class="number">
                    {total_mensajes}
                </div>
            </div>

            <div class="card">
                <h3>👥 Clientes</h3>
                <div class="number">
                    {total_clientes}
                </div>
            </div>

            <div class="card">
                <h3>📅 Citas</h3>
                <div class="number">
                    {total_citas}
                </div>
            </div>

        </div>

        <div class="menu">

            <a href="/clientes">
                👥 Ver clientes
            </a>

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
# 🔥 CLIENTES
# =========================
@main.route("/clientes")
def ver_clientes():

    if "tipo" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, cliente
        FROM clientes
        WHERE tipo = %s
        ORDER BY id DESC
    """, (tipo,))

    datos = cursor.fetchall()

    conn.close()

    html = f"""
    <h2>👥 Clientes ({tipo})</h2>
    <hr>
    """

    if not datos:
        html += "No hay clientes aún"

    for cliente_id, cliente in datos:

        html += f"""
        <div style="
            background:white;
            padding:15px;
            margin-bottom:10px;
            border-radius:10px;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
        ">
            📱 {cliente}

            <br><br>

            <a href="/eliminar_cliente?username={cliente}"
               style="
               background:red;
               color:white;
               padding:8px 12px;
               text-decoration:none;
               border-radius:8px;
               ">
               ❌ Eliminar
            </a>
        </div>
        """

    return html

# =========================
# 🔥 WEBHOOK
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

        from database import (
            guardar_cita,
            obtener_negocio_por_cliente
        )

        # =========================
        # 🔥 NEGOCIO
        # =========================
        negocio = obtener_negocio_por_cliente(user_number)

        if not negocio:
            negocio = numero_twilio

        print(f"🏢 NEGOCIO: {negocio}")

        # =========================
        # 🔥 GUARDAR
        # =========================
        registrar_cliente(user_number, negocio)

        guardar_usuario(
            user_number,
            incoming_msg,
            negocio
        )

        resp = MessagingResponse()
        msg = resp.message()

        # =========================
        # 🔥 ESTADO DB
        # =========================
        estado = obtener_estado(user_number)

        # =========================
        # 🔥 CONFIRMAR CITA
        # =========================
        if estado == "esperando_fecha":

            guardar_estado(user_number, "")

            guardar_cita(
                user_number,
                negocio,
                incoming_msg
            )

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

            guardar_estado(
                user_number,
                "esperando_fecha"
            )

            msg.body(
                "📅 Perfecto 👌\n\n"
                "Escribe fecha y hora:\n"
                "Ej: 10 mayo 3pm"
            )

            return str(resp)

        # =========================
        # 🔥 RESPUESTA
        # =========================
        respuesta = obtener_respuesta(
            negocio,
            incoming_msg
        )

        if not respuesta:
            respuesta = obtener_respuesta(
                negocio,
                "hola"
            )

        if not respuesta:
            respuesta = "👋 Hola, el bot está activo"

        msg.body(respuesta)

        print("✅ RESPUESTA ENVIADA")

        return str(resp)

    except Exception as e:

        print("❌ ERROR WEBHOOK:", str(e))

        resp = MessagingResponse()

        resp.message("❌ Error interno")

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

    html = f"<h2>📅 Citas ({tipo})</h2><hr>"

    for cliente, fecha, estado, creado in datos:

        html += f"""
        👤 {cliente}<br>
        📅 {fecha}<br>
        📌 {estado}<br>
        🕒 {creado}<br><hr>
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

    html = f"<h2>📋 Respuestas ({numero})</h2><hr>"

    for palabra, respuesta in datos:

        html += f"""
        <b>{palabra}</b><br><br>

        {respuesta}<br><br>

        <a href="/eliminar?palabra={palabra}">
            ❌ Eliminar
        </a>

        <hr>
        """

    return html

# =========================
# 🔥 AGREGAR RESPUESTA
# =========================
@main.route("/agregar_form")
def agregar_form():

    if "tipo" not in session:
        return redirect("/login")

    return """
    <h2>➕ Nueva respuesta</h2>

    <form action="/agregar">

        Palabra:<br>
        <input name="palabra"><br><br>

        Respuesta:<br>
        <textarea name="respuesta"
        rows="8"
        cols="40"></textarea><br><br>

        <button>
            Guardar
        </button>

    </form>
    """

@main.route("/agregar")
def agregar():

    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]

    palabra = request.args.get("palabra")
    respuesta = request.args.get("respuesta")

    guardar_respuesta(
        numero,
        palabra,
        respuesta
    )

    return redirect("/respuestas")

# =========================
# 🔥 ELIMINAR RESPUESTA
# =========================
@main.route("/eliminar")
def eliminar():

    if "tipo" not in session:
        return redirect("/login")

    numero = session["tipo"]

    palabra = request.args.get("palabra")

    eliminar_respuesta(
        numero,
        palabra
    )

    return redirect("/respuestas")

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