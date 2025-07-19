from flask import Blueprint, render_template, redirect, url_for, flash, request
from . import db, bcrypt
from .models import Usuario
from flask_login import login_user, logout_user, login_required
from . import login_manager

auth = Blueprint('auth', __name__)

# Cargar usuario por ID (para Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and bcrypt.check_password_hash(usuario.contraseña, contraseña):
            if not usuario.estado:
                flash('Tu cuenta está bloqueada. Contacta con un administrador.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(usuario)
            return redirect(url_for('main.inicio'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')

@auth.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        rol = request.form['rol']

        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado', 'warning')
            return redirect(url_for('auth.registro'))

        hash_pass = bcrypt.generate_password_hash(contraseña).decode('utf-8')
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, contraseña=hash_pass, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario registrado correctamente', 'success')
        return redirect(url_for('auth.login'))

    return render_template('registro.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('auth.login'))
