from . import db
from flask_login import UserMixin
from datetime import datetime

# -----------------------------
# Modelo Usuario
# -----------------------------
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, vendedor, cliente
    estado = db.Column(db.Boolean, default=True)    # ✅ Activo o bloqueado

    def __repr__(self):
        return f'<Usuario {self.nombre} - {self.rol}>'

# -----------------------------
# Modelo Producto
# -----------------------------
class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(100))  # ✅ Para guardar nombre de la imagen

    def __repr__(self):
        return f'<Producto {self.nombre}>'

# -----------------------------
# Modelo Venta
# -----------------------------
class Venta(db.Model):
    __tablename__ = 'ventas'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)

    detalles = db.relationship('DetalleVenta', backref='venta', cascade="all, delete-orphan")

# -----------------------------
# Modelo DetalleVenta
# -----------------------------
class DetalleVenta(db.Model):
    __tablename__ = 'detalles_venta'

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    producto = db.relationship('Producto')  # ✅ Relación directa para acceder al producto

# -----------------------------
# Modelo DeUsuario
# -----------------------------

