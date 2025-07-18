import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Producto, db
from .models import Producto, Venta, DetalleVenta, db
from flask import session
from werkzeug.utils import secure_filename
from flask import render_template, request
from .models import Producto, DetalleVenta
from datetime import datetime
from collections import defaultdict
from . import db
from flask_login import login_required
import random
from .models import Producto, Venta, DetalleVenta, db
from flask_login import login_required, current_user
from flask import Blueprint
main = Blueprint('main', __name__)  # 🔴 Esto debe ir arriba, antes de usar @main.route


@main.route('/')
@login_required
def inicio():
    # Ver si el admin activó simulación de vista
    rol = session.get('vista_simulada', current_user.rol)

    if rol == 'admin':
        # Datos para panel resumen
        total_productos = Producto.query.count()
        total_ventas = Venta.query.count()
        ingresos = db.session.query(db.func.sum(Venta.total)).scalar() or 0

        # Producto más vendido
        mas_vendido = db.session.query(
            DetalleVenta.producto_id,
            db.func.sum(DetalleVenta.cantidad).label('cantidad_total')
        ).group_by(DetalleVenta.producto_id)\
         .order_by(db.desc('cantidad_total'))\
         .first()

        producto_mas_vendido = Producto.query.get(mas_vendido.producto_id) if mas_vendido else None

        return render_template('dashboard_admin.html',
                               usuario=current_user,
                               total_productos=total_productos,
                               total_ventas=total_ventas,
                               ingresos=ingresos,
                               producto_mas_vendido=producto_mas_vendido)

    elif rol == 'vendedor':
        return render_template('dashboard_vendedor.html', usuario=current_user)
    else:
        return render_template('dashboard_cliente.html', usuario=current_user)

@main.route('/cambiar_vista/<rol_simulado>')
@login_required
def cambiar_vista(rol_simulado):
    if current_user.rol != 'admin':
        flash('Solo el admin puede cambiar de vista', 'danger')
        return redirect(url_for('main.inicio'))

    if rol_simulado not in ['admin', 'vendedor', 'cliente']:
        flash('Vista inválida', 'warning')
        return redirect(url_for('main.inicio'))

    session['vista_simulada'] = rol_simulado
    flash(f'Ahora estás viendo como: {rol_simulado}', 'info')
    return redirect(url_for('main.inicio'))


# Rutas de productos (después de definir main)
@main.route('/productos')
@login_required
def lista_productos():
    if current_user.rol not in ['admin', 'vendedor']:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.inicio'))

    productos = Producto.query.all()
    rol = session.get('vista_simulada', current_user.rol)  # ✅ ESTA LÍNEA ES CLAVE
    return render_template('productos.html', productos=productos, rol=rol)

@main.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto():
    rol = session.get('vista_simulada', current_user.rol)
    if rol not in ['admin', 'vendedor']:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.inicio'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])

        imagen_file = request.files.get('imagen')
        imagen_nombre = None
        if imagen_file and imagen_file.filename != '':
            imagen_nombre = secure_filename(imagen_file.filename)
            ruta = os.path.join('app', 'static', 'uploads', imagen_nombre)
            imagen_file.save(ruta)

        nuevo = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            imagen=imagen_nombre
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto creado correctamente', 'success')
        return redirect(url_for('main.lista_productos'))

    return render_template('crear_producto.html', rol=rol)


@main.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    rol = session.get('vista_simulada', current_user.rol)
    if rol not in ['admin', 'vendedor']:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.inicio'))

    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])

        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('main.lista_productos'))

    return render_template('editar_producto.html', producto=producto, rol=rol)

@main.route('/productos/eliminar/<int:id>')
@login_required
def eliminar_producto(id):
    rol = session.get('vista_simulada', current_user.rol)
    if rol not in ['admin', 'vendedor']:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.inicio'))

    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado', 'success')
    return redirect(url_for('main.lista_productos'))

@main.route('/ventas/registrar', methods=['GET', 'POST'])
@login_required
def registrar_venta():
    rol = session.get('vista_simulada', current_user.rol)
    if rol not in ['admin', 'vendedor']:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.inicio'))

    productos = Producto.query.all()

    if request.method == 'POST':
        total = 0
        detalles = []

        for producto in productos:
            cantidad = int(request.form.get(f'cantidad_{producto.id}', 0))
            if cantidad > 0:
                if cantidad > producto.stock:
                    flash(f"No hay suficiente stock para {producto.nombre}", 'danger')
                    return redirect(url_for('main.registrar_venta'))

                subtotal = producto.precio * cantidad
                total += subtotal

                detalles.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })

        if not detalles:
            flash('Debes seleccionar al menos un producto.', 'warning')
            return redirect(url_for('main.registrar_venta'))

        venta = Venta(total=total)
        db.session.add(venta)
        db.session.flush()

        for item in detalles:
            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=item['producto'].id,
                cantidad=item['cantidad'],
                subtotal=item['subtotal']
            )
            db.session.add(detalle)
            item['producto'].stock -= item['cantidad']

        db.session.commit()
        flash('Venta registrada con éxito', 'success')
        return redirect(url_for('main.lista_ventas'))

    return render_template('registrar_venta.html', productos=productos)

@main.route('/ventas')
@login_required
def lista_ventas():
    rol = session.get('vista_simulada', current_user.rol)
    if rol not in ['admin', 'vendedor']:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.inicio'))

    desde = request.args.get('desde')
    hasta = request.args.get('hasta')

    query = Venta.query

    if desde:
        query = query.filter(Venta.fecha >= desde)
    if hasta:
        query = query.filter(Venta.fecha <= hasta)

    ventas = query.order_by(Venta.fecha.desc()).all()
    return render_template('ventas.html', ventas=ventas)



@main.route('/reportes', methods=['GET', 'POST'])
@login_required
def reportes():
    productos = Producto.query.all()
    grafico_datos = defaultdict(list)

    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fin = fin.replace(hour=23, minute=59, second=59)  # 🔧 INCLUYE TODO EL DÍA

        detalles = db.session.query(
            DetalleVenta.producto_id,
            db.func.sum(DetalleVenta.cantidad).label('cantidad'),
            db.func.strftime('%Y-%m-%d', Venta.fecha).label('fecha')
        ).join(Venta)\
        .filter(Venta.fecha >= inicio, Venta.fecha <= fin)\
        .group_by(DetalleVenta.producto_id, 'fecha')\
        .all()

        for producto_id, cantidad, fecha in detalles:
            nombre_producto = Producto.query.get(producto_id).nombre
            grafico_datos[nombre_producto].append({
                'fecha': fecha,
                'cantidad': cantidad
            })

    return render_template('reportes.html', productos=productos, grafico_datos=grafico_datos)
