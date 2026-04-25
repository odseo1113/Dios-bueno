import app
print("🔥 APP IMPORTADA DESDE:", app.__file__)

from app import create_app
app = create_app()

