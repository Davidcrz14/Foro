from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from flask_socketio import SocketIO, emit
from database import agregar_mensaje, obtener_mensajes, registrar_usuario, verificar_usuario, obtener_usuarios_conectados, inicializar_db, obtener_usuario_por_id, actualizar_perfil, agregar_columna_descripcion
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

inicializar_db()  # Inicialización de la base de datos

nombres_aleatorios = ["Anónimo", "Incógnito", "Misterioso", "Desconocido", "Enigma"]

def handle_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error('Error: %s', (e))
            return jsonify(error=str(e)), 500
    return decorated_function

@app.errorhandler(500)
def internal_error(error):
    app.logger.error('Server Error: %s', (error))
    return jsonify(error=str(error)), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify(error=str(error)), 404

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('register'))
    usuarios_conectados = obtener_usuarios_conectados()
    return render_template('index.html', usuarios_conectados=usuarios_conectados)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        registrar_usuario(nombre, correo, contraseña)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario_id = verificar_usuario(correo, contraseña)
        if usuario_id:
            session['usuario_id'] = usuario_id
            return redirect(url_for('index'))
        return "Credenciales inválidas", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))

@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    if 'usuario_id' not in session:
        return jsonify({"success": False, "error": "No autorizado"}), 401
    mensaje = request.form['mensaje']
    agregar_mensaje(session['usuario_id'], mensaje)
    return jsonify({"success": True})

@app.route('/obtener_mensajes')
@handle_exceptions
def get_mensajes():
    mensajes = obtener_mensajes()
    mensajes_serializados = [
        {
            'id': m[0],
            'nombre': m[1],
            'mensaje': m[2],
            'fecha': m[3].isoformat() if isinstance(m[3], datetime) else m[3]
        }
        for m in mensajes
    ]
    mensajes_serializados.sort(key=lambda x: x['fecha'])  # Ordenar cronológicamente
    return jsonify(mensajes_serializados)

@app.route('/usuarios_conectados')
@handle_exceptions
def get_usuarios_conectados():
    usuarios = obtener_usuarios_conectados()
    return jsonify(usuarios)

@socketio.on('connect')
def handle_connect():
    if 'usuario_id' not in session:
        return False
    emit('usuarios_conectados', obtener_usuarios_conectados(), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    emit('usuarios_conectados', obtener_usuarios_conectados(), broadcast=True)

@socketio.on('solicitar_usuarios_conectados')
def handle_solicitar_usuarios_conectados():
    emit('usuarios_conectados', obtener_usuarios_conectados())

@socketio.on('enviar_mensaje')
def handle_mensaje(data):
    if 'usuario_id' not in session:
        emit('error', {'message': 'No autorizado'})
        return

    mensaje = data['mensaje']
    agregar_mensaje(session['usuario_id'], mensaje)
    mensajes = obtener_mensajes()
    mensajes_serializados = [
        {
            'id': m[0],
            'nombre': m[1],
            'mensaje': m[2],
            'fecha': m[3].isoformat() if isinstance(m[3], datetime) else m[3]
        }
        for m in mensajes
    ]
    mensajes_serializados.sort(key=lambda x: x['fecha'])
    emit('nuevo_mensaje', mensajes_serializados, broadcast=True)

@app.route('/perfil/<int:usuario_id>')
def ver_perfil(usuario_id):
    usuario = obtener_usuario_por_id(usuario_id)
    if usuario:
        return render_template('perfil.html', usuario=usuario)
    else:
        return "Usuario no encontrado", 404

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = obtener_usuario_por_id(session['usuario_id'])
    if not usuario:
        return "Usuario no encontrado", 404

    if request.method == 'POST':
        descripcion = request.form.get('descripcion', usuario['descripcion'])
        sexo = request.form.get('sexo', usuario['sexo'])
        edad = request.form.get('edad', usuario['edad'])
        foto_perfil_url = request.form.get('foto_perfil_url')

        if foto_perfil_url:
            foto_perfil = foto_perfil_url
        elif 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                foto_perfil = url_for('uploaded_file', filename=filename, _external=True)
            else:
                foto_perfil = usuario['foto_perfil']
        else:
            foto_perfil = usuario['foto_perfil']

        actualizar_perfil(session['usuario_id'], descripcion, sexo, edad, foto_perfil)
        return redirect(url_for('ver_perfil', usuario_id=session['usuario_id']))

    return render_template('editar_perfil.html', usuario=usuario)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if __name__ == '__main__':
    inicializar_db()
    agregar_columna_descripcion()
    socketio.run(app, debug=True)
