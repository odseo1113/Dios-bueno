from flask import Flask
from database import init_db

print("🔥🔥🔥 INIT REAL EJECUTADO 🔥🔥🔥")

def create_app():
    app = Flask(__name__)

    # 🔐 CLAVE PARA SESIONES (LOGIN)
    app.secret_key = "superclave123"

    # 🔥 RECOMENDADO PARA PRODUCCIÓN (EVITA PROBLEMAS DE SESIÓN EN RAILWAY)
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # 🔥 Inicializar DB (AQUÍ YA SE CREA TODO: tablas + pool)
    with app.app_context():
        try:
            init_db()
            print("✅ Base de datos inicializada correctamente (incluye pool Twilio)")
        except Exception as e:
            print("❌ ERROR init_db:", e)

    from .routes import main
    app.register_blueprint(main)

    # 🔥 DEBUG CLAVE
    print("🔥 RUTAS REGISTRADAS:")
    print(app.url_map)

    return app