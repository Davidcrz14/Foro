import sqlite3
from datetime import datetime

DATABASE = 'foro.db'

def inicializar_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL,
        contraseña TEXT NOT NULL,
        descripcion TEXT,
        sexo TEXT,
        edad INTEGER,
        foto_perfil TEXT,
        spotify_url TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mensajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        mensaje TEXT NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    ''')

    conn.commit()
    conn.close()

def agregar_mensaje(usuario_id, mensaje):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO mensajes (usuario_id, mensaje, fecha)
    VALUES (?, ?, ?)
    ''', (usuario_id, mensaje, datetime.now()))

    conn.commit()
    conn.close()

def obtener_mensajes():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT mensajes.id, usuarios.nombre, mensajes.mensaje, mensajes.fecha
    FROM mensajes
    JOIN usuarios ON mensajes.usuario_id = usuarios.id
    ''')

    mensajes = cursor.fetchall()
    conn.close()
    return mensajes

def registrar_usuario(nombre, correo, contraseña):
    try:
        conn = sqlite3.connect(DATABASE, timeout=20)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO usuarios (nombre, correo, contraseña)
        VALUES (?, ?, ?)
        ''', (nombre, correo, contraseña))

        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error al registrar usuario: {e}")
        conn.rollback()
    finally:
        conn.close()

def verificar_usuario(correo, contraseña):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id FROM usuarios
    WHERE correo = ? AND contraseña = ?
    ''', (correo, contraseña))

    usuario = cursor.fetchone()
    conn.close()

    return usuario[0] if usuario else None

def obtener_usuarios_conectados():
    with sqlite3.connect(DATABASE, timeout=20) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, nombre FROM usuarios')
        usuarios = cursor.fetchall()
    return [{'id': u[0], 'nombre': u[1]} for u in usuarios]

def obtener_usuario_por_id(usuario_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, nombre, correo, descripcion, sexo, edad, foto_perfil, spotify_url
    FROM usuarios
    WHERE id = ?
    ''', (usuario_id,))

    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        return {
            'id': usuario[0],
            'nombre': usuario[1],
            'correo': usuario[2],
            'descripcion': usuario[3],
            'sexo': usuario[4],
            'edad': usuario[5],
            'foto_perfil': usuario[6],
            'spotify_url': usuario[7]
        }
    return None

def actualizar_perfil(usuario_id, descripcion, sexo, edad, foto_perfil, spotify_url):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE usuarios
    SET descripcion = ?, sexo = ?, edad = ?, foto_perfil = ?, spotify_url = ?
    WHERE id = ?
    ''', (descripcion, sexo, edad, foto_perfil, spotify_url, usuario_id))

    conn.commit()
    conn.close()

def agregar_columna_descripcion():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('ALTER TABLE usuarios ADD COLUMN descripcion TEXT')
        conn.commit()
        print("Columna 'descripcion' agregada con éxito.")
    except sqlite3.OperationalError:
        print("La columna 'descripcion' ya existe.")

    conn.close()

def agregar_columna_spotify_url():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('ALTER TABLE usuarios ADD COLUMN spotify_url TEXT')
        conn.commit()
        print("Columna 'spotify_url' agregada con éxito.")
    except sqlite3.OperationalError:
        print("La columna 'spotify_url' ya existe.")

    conn.close()
