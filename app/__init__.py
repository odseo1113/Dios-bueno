from flask import Flask
from database import init_db
import os

print("🔥🔥🔥 INIT REAL EJECUTADO 🔥🔥🔥")

def create_app():
    app = Flask(__name__)

    print("🔥 APP IMPORTADA DESDE:", __file__)

    # 🔐 CLAVE SEGURA (usa variable de entorno en producción)
    app.secret_key = os.getenv("SECRET_KEY", "dev_super_secret_key")

    # 🔥 CONFIG COOKIES (PRODUCCIÓN)
    app.config["SESSION_COOKIE_SECURE"] = True  # en Railway HTTPS funciona bien
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # 🔥 IMPORTANTE (evita errores con proxies como Railway)
    app.config["PREFERRED_URL_SCHEME"] = "https"

    # 🔥 Inicializar DB (tablas + pool Twilio + citas)
    with app.app_context():
        try:
            init_db()
            print("✅ Base de datos inicializada correctamente (incluye pool Twilio + citas)")
        except Exception as e:
            print("❌ ERROR init_db:", e)

    # 🔥 BLUEPRINT
    from .routes import main
    app.register_blueprint(main)

    # 🔥 DEBUG CLAVE
    print("🔥 RUTAS REGISTRADAS:")
    print(app.url_map)

    return app