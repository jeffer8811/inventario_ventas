# init_db.py
from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("📦 Base de datos recreada correctamente.")
