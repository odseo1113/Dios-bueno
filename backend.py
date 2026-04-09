from flask import Flask, request, jsonify
from flask_cors import CORS  # 👈 IMPORTANTE

app = Flask(__name__)
CORS(app)  # 👈 ESTO VA AQUÍ (debajo de app)

def responder(mensaje):
    mensaje = mensaje.lower()

    if "inscripcion" in mensaje:
        return "Las inscripciones están abiertas hasta el 30 de julio."
    elif "costos" in mensaje:
        return "Los costos van desde $500 USD por semestre."
    elif "carreras" in mensaje:
        return "Tenemos Ingeniería, Administración y Contaduría."
    else:
        return "¿Quieres información sobre inscripciones, costos o carreras?"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensaje = data.get("mensaje", "")
    respuesta = responder(mensaje)
    return jsonify({"respuesta": respuesta})

# 👇 ESTA PARTE VA SIEMPRE AL FINAL
if __name__ == "__main__":
    app.run(debug=True)