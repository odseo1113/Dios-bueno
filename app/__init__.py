from flask import Flask
from database import init_db

def create_app():
    app = Flask(__name__)

    app.secret_key = "superclave123"

    # 🔥 DB aquí, no en run.py
    init_db()

    from .routes import main
    app.register_blueprint(main)

    return app