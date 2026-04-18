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

main = Blueprint('main', __name__)


# 🔹 Home
@main.route("/")
def home():
    return "OK"


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


# 🔥 CREAR USUARIOS EXTRA
@main.route("/crear_users_extra")
def crear_users_extra():
    from database import crear_cuenta

    try:
        crear_cuenta("peluqueria", "1234", "peluqueria")
        crear_cuenta("canina", "1234", "peluqueria_canina")
    except:
        pass

    return "✅ usuarios peluquería creados"


# 🔥 CREAR CLIENTES EXTRA
@main.route("/crear_clientes_extra")
def crear_clientes_extra():
    from database import registrar_cliente

    registrar_cliente("whatsapp:+3333", "peluqueria")
    registrar_cliente("whatsapp:+4444", "peluqueria_canina")

    return "✅ clientes peluquería creados"


# 🔹 WEBHOOK (🔥 MODO PRUEBA CORREGIDO)
@main.route("/webhook", methods=["POST"])
def webhook():
    user_number = request.form.get("From", "")
    incoming_msg = request.form.get("Body", "").lower()

    # 🔥 DETECCIÓN SEGURA
    if "test1" in incoming_msg:
        tipo_cliente = "peluqueria"

    elif "test2" in incoming_msg:
        tipo_cliente = "peluqueria_canina"

    else:
        tipo_cliente = obtener_tipo_por_numero(user_number)

        if not tipo_cliente:
            registrar_cliente(user_number, "abogado")
            tipo_cliente = "abogado"

    # 🔥 LIMPIEZA FINAL (CLAVE)
    incoming_msg = (
        incoming_msg
        .replace("test1", "")
        .replace("test2", "")
        .strip()
    )

    guardar_usuario(user_number, incoming_msg, tipo_cliente)

    resp = MessagingResponse()
    msg = resp.message()

    respuesta = obtener_respuesta(tipo_cliente, incoming_msg)

    if respuesta:
        msg.body(respuesta)
    else:
        if "hola" in incoming_msg:
            msg.body("👋 Bienvenido\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita")
        elif incoming_msg == "1":
            msg.body("Servicios disponibles")
        elif incoming_msg == "2":
            msg.body("Información de precios")
        elif incoming_msg == "3":
            msg.body("Agenda tu cita")
        else:
            msg.body("Escribe 'hola'")

    return str(resp)


# 🔐 LOGIN
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = validar_usuario(
            request.form["username"],
            request.form["password"]
        )

        if user:
            session["user"] = user[1]
            session["tipo"] = user[3]
            return redirect("/dashboard")

        return "❌ Credenciales incorrectas"

    return render_template("login.html")


# 🔐 DASHBOARD
@main.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    usuarios = obtener_por_tipo(tipo)
    total = contar_por_tipo(tipo)

    return render_template(
        "clientes.html",
        usuarios=usuarios,
        total=total
    )


# 🔥 PANEL DE RESPUESTAS
@main.route("/respuestas", methods=["GET", "POST"])
def respuestas():
    if "user" not in session:
        return redirect("/login")

    tipo = session["tipo"]

    if request.method == "POST":
        palabra = request.form["palabra"].lower()
        respuesta = request.form["respuesta"]

        guardar_respuesta(tipo, palabra, respuesta)

    lista_respuestas = obtener_respuestas(tipo)

    return render_template(
        "respuestas.html",
        respuestas=lista_respuestas
    )


# 🗑️ ELIMINAR RESPUESTA
@main.route("/eliminar_respuesta/<int:id>")
def eliminar_respuesta_route(id):
    if "user" not in session:
        return redirect("/login")

    eliminar_respuesta(id)
    return redirect("/respuestas")


# 🔄 DATOS
@main.route("/datos")
def datos():
    if "user" not in session:
        return ""

    tipo = session["tipo"]
    usuarios = obtener_por_tipo(tipo)
    total = contar_por_tipo(tipo)

    html = ""
    interesados = 0

    for u in usuarios:
        estado = "⚪ Normal"
        clase = ""

        if u[2] == "2":
            estado = "🟢 Interesado"
            clase = "interesado"
            interesados += 1

        html += f"""
        <tr class="{clase}">
            <td>{u[0]}</td>
            <td>{u[1]}</td>
            <td>{u[2]}</td>
            <td>{u[4]}</td>
            <td>{estado}</td>
        </tr>
        """

    return f"{html}|{total}|{interesados}"


# 🔐 LOGOUT
@main.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# 📤 EXPORTAR
@main.route("/exportar")
def exportar():
    if "user" not in session:
        return redirect("/login")

    tipo = session["tipo"]
    usuarios = obtener_por_tipo(tipo)

    df = pd.DataFrame(
        usuarios,
        columns=["ID", "Número", "Mensaje", "Tipo", "Fecha"]
    )

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(output, download_name="clientes.xlsx", as_attachment=True)