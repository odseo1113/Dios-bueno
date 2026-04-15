from flask import Blueprint, request, render_template, send_file, session, redirect
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    guardar_usuario,
    obtener_por_tipo,
    contar_por_tipo,
    validar_usuario,
    obtener_tipo_por_numero,
    registrar_cliente
)

import pandas as pd
from io import BytesIO

main = Blueprint('main', __name__)


# 🔹 Home
@main.route("/")
def home():
    return "OK"


# 🔹 Webhook (MULTI CLIENTE 🔥)
@main.route("/webhook", methods=["POST"])
def webhook():
    user_number = request.form.get("From", "")
    incoming_msg = request.form.get("Body", "").strip().lower()

    # 🔥 Obtener tipo desde DB
    tipo_cliente = obtener_tipo_por_numero(user_number)

    # 🔥 Si no existe, registrarlo automáticamente
    if not tipo_cliente:
        registrar_cliente(user_number, "abogado")
        tipo_cliente = "abogado"

    # Guardar mensaje
    guardar_usuario(user_number, incoming_msg, tipo_cliente)

    resp = MessagingResponse()
    msg = resp.message()

    # 🔥 Lógica por tipo de cliente
    if tipo_cliente == "abogado":

        if "hola" in incoming_msg:
            msg.body("👋 Bienvenido al consultorio jurídico ⚖️\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita")

        elif incoming_msg == "1":
            msg.body("⚖️ Derecho laboral, civil, familiar")

        elif incoming_msg == "2":
            msg.body("💰 Desde $50.000 COP")

        elif incoming_msg == "3":
            msg.body("📅 Envíanos tus datos para agendar")

        else:
            msg.body("Escribe 'hola'")

    else:
        msg.body("👋 Hola, escribe 'hola' para iniciar")

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