import sqlite3
import hashlib
from datetime import datetime
import math
import hashlib

DB_NAME = "estacionamiento.db"


def get_connection():
    """Devuelve una conexión a la base de datos con las foreign keys activadas."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # permite acceder a las columnas por nombre
    return conn


def init_db():
    """Crea las tablas si no existen y un usuario administrador por defecto."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL CHECK (rol IN ('admin', 'conductor'))
        )
    """)

    # Cada fila es una "empresa" de estacionamiento (un predio con sus propios lugares)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estacionamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lugares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL,
            tipo_vehiculo TEXT NOT NULL CHECK (tipo_vehiculo IN ('auto', 'moto', 'camioneta')),
            precio_hora REAL NOT NULL,
            disponible INTEGER NOT NULL DEFAULT 1,
            estacionamiento_id INTEGER NOT NULL,
            FOREIGN KEY (estacionamiento_id) REFERENCES estacionamientos(id) ON DELETE CASCADE,
            UNIQUE (numero, estacionamiento_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lugar_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            fecha_reserva TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'finalizada', 'cancelada')),
            FOREIGN KEY (lugar_id) REFERENCES lugares(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    # Usuario admin por defecto para poder entrar la primera vez
    cur.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)",
            ("admin", encriptar_dato("admin123"), "Administrador", "admin"),
        )

    # Un par de estacionamientos de ejemplo, para no arrancar con la lista vacía
    cur.execute("SELECT COUNT(*) AS total FROM estacionamientos")
    if cur.fetchone()["total"] == 0:
        cur.executemany(
            "INSERT INTO estacionamientos (nombre, direccion) VALUES (?, ?)",
            [
                ("Estacionamiento Cine Santa Fe", "Rivera 1111"),
                ("Estacionamientos Matuka", "San Jeronimo Norte 1211"),
                ("Terminal Norte", "Km 25"),
            ],
        )

    conn.commit()
    conn.close()



# USUARIOS
def crear_usuario(username, password, nombre, rol):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)",
            (username, encriptar_dato(password), nombre, rol),
        )
        conn.commit()
        return True, "Usuario creado correctamente"
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe"
    finally:
        conn.close()


def validar_login(username, password):
    """Devuelve la fila del usuario si las credenciales son correctas, sino None."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Encriptamos la contraseña ingresada
    clave_hash = encriptar_dato(password)
    
    try:
        # Inspeccionamos las columnas para soportar tanto 'username'/'password' como 'usuario'/'clave'
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas = [row[1] for row in cursor.fetchall()]
        
        col_usr = "username" if "username" in columnas else "usuario"
        col_clave = "password" if "password" in columnas else "clave"

        # Buscamos comparando la contraseña encriptada (o plana para usuarios viejos)
        query = f"""
            SELECT * FROM usuarios 
            WHERE LOWER({col_usr}) = LOWER(?) 
            AND ({col_clave} = ? OR {col_clave} = ?)
        """
        cursor.execute(query, (username, clave_hash, password))
        usuario = cursor.fetchone()
        conn.close()
        return usuario
    except Exception as e:
        conn.close()
        print(f"Error en validar_login: {e}")
        return None


# 1. Función para asegurar que la tabla 'usuarios' tenga los campos 'email' y 'dni'
def preparar_tabla_usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN dni TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()

# 2. Función de registro con validaciones específicas
def registrar_usuario(nombre, usuario, clave, email, dni, rol="conductor"):
    nombre = nombre.strip() if nombre else ""
    usuario = usuario.strip() if usuario else ""
    clave = clave.strip() if clave else ""
    email = email.strip() if email else ""
    dni = dni.strip() if dni else ""

    # 1. Validaciones sobre el texto plano
    if not nombre or not usuario or not clave or not email or not dni:
        return False, "Todos los campos son obligatorios."

    if not dni.isdigit() or len(dni) != 8:
        return False, "El DNI debe tener exactamente 8 dígitos numéricos."

    if len(clave) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas = [row[1] for row in cursor.fetchall()]

        # Encriptamos el DNI para la búsqueda duplicada si estuviera encriptado en BD
        dni_hash = encriptar_dato(dni)
        clave_hash = encriptar_dato(clave)

        # Verificación de usuario duplicado
        col_usr_check = "username" if "username" in columnas else "usuario"
        cursor.execute(f"SELECT id FROM usuarios WHERE LOWER({col_usr_check}) = LOWER(?)", (usuario,))
        if cursor.fetchone():
            conn.close()
            return False, "El nombre de usuario ya está en uso."

        # Verificación de correo duplicado
        if "email" in columnas:
            cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = LOWER(?)", (email,))
            if cursor.fetchone():
                conn.close()
                return False, "El correo electrónico ya está en uso."

        # Inserción guardando HASH de clave y DNI
        cols_insert = []
        vals_insert = []

        if "username" in columnas:
            cols_insert.append("username")
            vals_insert.append(usuario)
        if "usuario" in columnas:
            cols_insert.append("usuario")
            vals_insert.append(usuario)

        if "password" in columnas:
            cols_insert.append("password")
            vals_insert.append(clave_hash)
        if "clave" in columnas:
            cols_insert.append("clave")
            vals_insert.append(clave_hash)

        if "nombre" in columnas:
            cols_insert.append("nombre")
            vals_insert.append(nombre)
        if "rol" in columnas:
            cols_insert.append("rol")
            vals_insert.append(rol)
        if "email" in columnas:
            cols_insert.append("email")
            vals_insert.append(email)
        if "dni" in columnas:
            cols_insert.append("dni")
            vals_insert.append(dni_hash)

        placeholders = ", ".join(["?"] * len(vals_insert))
        str_cols = ", ".join(cols_insert)

        cursor.execute(f"INSERT INTO usuarios ({str_cols}) VALUES ({placeholders})", vals_insert)
        
        conn.commit()
        conn.close()
        return True, "Registro exitoso. Ahora podés iniciar sesión."

    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {e}"

# ESTACIONAMIENTOS
def obtener_estacionamientos():
    conn = get_connection()
    cur = conn.execute("SELECT * FROM estacionamientos ORDER BY nombre")
    estacionamientos = cur.fetchall()
    conn.close()
    return estacionamientos


def obtener_estacionamiento_por_id(estacionamiento_id):
    conn = get_connection()
    cur = conn.execute("SELECT * FROM estacionamientos WHERE id = ?", (estacionamiento_id,))
    estacionamiento = cur.fetchone()
    conn.close()
    return estacionamiento


def contar_lugares(estacionamiento_id):
    """Devuelve (total_lugares, lugares_disponibles) de un estacionamiento, para mostrar en la card."""
    conn = get_connection()
    cur = conn.execute(
        """SELECT COUNT(*) AS total, SUM(disponible) AS disponibles
           FROM lugares WHERE estacionamiento_id = ?""",
        (estacionamiento_id,),
    )
    fila = cur.fetchone()
    conn.close()
    total = fila["total"] or 0
    disponibles = fila["disponibles"] or 0
    return total, disponibles


def agregar_estacionamiento(nombre, direccion):
    conn = get_connection()
    conn.execute(
        "INSERT INTO estacionamientos (nombre, direccion) VALUES (?, ?)",
        (nombre, direccion),
    )
    conn.commit()
    conn.close()
    return True, "Estacionamiento agregado correctamente"



# LUGARES
def agregar_lugar(numero, tipo_vehiculo, precio_hora, estacionamiento_id):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO lugares (numero, tipo_vehiculo, precio_hora, disponible, estacionamiento_id)
               VALUES (?, ?, ?, 1, ?)""",
            (numero, tipo_vehiculo, precio_hora, estacionamiento_id),
        )
        conn.commit()
        return True, "Lugar agregado correctamente"
    except sqlite3.IntegrityError:
        return False, "Ya existe un lugar con ese número en este estacionamiento"
    finally:
        conn.close()


def modificar_lugar(lugar_id, numero, tipo_vehiculo, precio_hora, disponible):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE lugares
               SET numero = ?, tipo_vehiculo = ?, precio_hora = ?, disponible = ?
               WHERE id = ?""",
            (numero, tipo_vehiculo, precio_hora, int(disponible), lugar_id),
        )
        conn.commit()
        return True, "Lugar actualizado correctamente"
    except sqlite3.IntegrityError:
        return False, "Ya existe un lugar con ese número"
    finally:
        conn.close()


def borrar_lugar(lugar_id):
    conn = get_connection()
    conn.execute("DELETE FROM lugares WHERE id = ?", (lugar_id,))
    conn.commit()
    conn.close()


def obtener_lugares(estacionamiento_id, solo_disponibles=False):
    """Lugares de UN estacionamiento puntual (siempre filtramos por estacionamiento_id)."""
    conn = get_connection()
    if solo_disponibles:
        cur = conn.execute(
            "SELECT * FROM lugares WHERE estacionamiento_id = ? AND disponible = 1 ORDER BY numero",
            (estacionamiento_id,),
        )
    else:
        cur = conn.execute(
            "SELECT * FROM lugares WHERE estacionamiento_id = ? ORDER BY numero",
            (estacionamiento_id,),
        )
    lugares = cur.fetchall()
    conn.close()
    return lugares


def obtener_lugar_por_id(lugar_id):
    conn = get_connection()
    cur = conn.execute("SELECT * FROM lugares WHERE id = ?", (lugar_id,))
    lugar = cur.fetchone()
    conn.close()
    return lugar



# RESERVAS
def reservar_lugar(lugar_id, usuario_id):
    """Marca el lugar como no disponible y crea el registro de reserva."""
    conn = get_connection()
    lugar = conn.execute("SELECT * FROM lugares WHERE id = ?", (lugar_id,)).fetchone()
    if lugar is None or lugar["disponible"] == 0:
        conn.close()
        return False, "El lugar ya no está disponible"

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO reservas (lugar_id, usuario_id, fecha_reserva, estado) VALUES (?, ?, ?, 'activa')",
        (lugar_id, usuario_id, fecha),
    )
    conn.execute("UPDATE lugares SET disponible = 0 WHERE id = ?", (lugar_id,))
    conn.commit()
    conn.close()
    return True, "Reserva realizada correctamente"


def cancelar_reserva(reserva_id):
    """Cancela la reserva y vuelve a liberar el lugar."""
    conn = get_connection()
    reserva = conn.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    if reserva is None:
        conn.close()
        return False, "Reserva no encontrada"

    conn.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
    conn.execute("UPDATE lugares SET disponible = 1 WHERE id = ?", (reserva["lugar_id"],))
    conn.commit()
    conn.close()
    return True, "Reserva cancelada, el lugar quedó disponible"


def obtener_reservas_usuario(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                r.id, 
                l.numero, 
                l.tipo_vehiculo, 
                e.nombre as estacionamiento_nombre, 
                r.fecha_reserva, 
                r.estado,
                COALESCE(r.monto_total, 0.0) as monto_total
            FROM reservas r
            JOIN lugares l ON r.lugar_id = l.id
            JOIN estacionamientos e ON l.estacionamiento_id = e.id
            WHERE r.usuario_id = ?
            ORDER BY r.id DESC
        """, (usuario_id,))
        rows = cursor.fetchall()
        conn.close()

        reservas = []
        for row in rows:
            if isinstance(row, dict):
                reservas.append(row)
            else:
                try:
                    dict_row = dict(row)
                except Exception:
                    dict_row = {
                        "id": row[0],
                        "numero": row[1],
                        "tipo_vehiculo": row[2],
                        "estacionamiento_nombre": row[3],
                        "fecha_reserva": row[4],
                        "estado": row[5],
                        "monto_total": row[6] if len(row) > 6 else 0.0
                    }
                reservas.append(dict_row)
        return reservas
    except Exception as e:
        conn.close()
        print(f"Error en obtener_reservas_usuario: {e}")
        return []


# 1. Asegura que la tabla reservas tenga los campos de cierre financiero
def preparar_tabla_facturacion():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE reservas ADD COLUMN fecha_fin TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE reservas ADD COLUMN monto_total REAL DEFAULT 0.0")
    except Exception:
        pass
    conn.commit()
    conn.close()

# 2. Finaliza la reserva, libera el lugar y calcula el cobro por horas transcurridas
def finalizar_reserva_y_cobrar(reserva_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT r.id, r.lugar_id, r.fecha_reserva, l.precio_hora 
            FROM reservas r 
            JOIN lugares l ON r.lugar_id = l.id 
            WHERE r.id = ? AND r.estado = 'activa'
        """, (reserva_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False, "Reserva no encontrada o ya finalizada."

        r_id, lugar_id, fecha_str, precio_hora = row
        
        # Conversión flexible de fecha
        try:
            fecha_limpia = str(fecha_str).split('.')[0]
            inicio = datetime.strptime(fecha_limpia, "%Y-%m-%d %H:%M:%S")
        except Exception:
            inicio = datetime.now()

        fin = datetime.now()
        
        # Cálculo de horas y precio
        segundos = (fin - inicio).total_seconds()
        horas_cobradas = max(1, math.ceil(segundos / 3600.0))
        monto_total = round(horas_cobradas * float(precio_hora), 2)
        fecha_fin_str = fin.strftime("%Y-%m-%d %H:%M:%S")

        # Guardar cobro y liberar lugar
        cursor.execute("""
            UPDATE reservas 
            SET estado = 'finalizada', fecha_fin = ?, monto_total = ? 
            WHERE id = ?
        """, (fecha_fin_str, monto_total, reserva_id))

        cursor.execute("UPDATE lugares SET disponible = 1 WHERE id = ?", (lugar_id,))
        
        conn.commit()
        conn.close()
        return True, f"Estadía finalizada ({horas_cobradas} hr(s)). Total a pagar: ${monto_total:.2f}"
    except Exception as e:
        conn.close()
        print(f"Error en cobro: {e}")  # Revisa la consola si ocurre un error
        return False, f"Error al procesar el cobro: {e}"

# 3. Obtiene el acumulado monetario (Hoy, Mes, Histórico) para la vista Admin
def obtener_resumen_recaudacion(estacionamiento_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    mes_str = datetime.now().strftime("%Y-%m")

    cursor.execute("""
        SELECT SUM(r.monto_total) FROM reservas r
        JOIN lugares l ON r.lugar_id = l.id
        WHERE l.estacionamiento_id = ? AND r.estado = 'finalizada' AND r.fecha_fin LIKE ?
    """, (estacionamiento_id, f"{hoy_str}%"))
    res_hoy = cursor.fetchone()
    hoy = res_hoy[0] if res_hoy and res_hoy[0] else 0.0

    cursor.execute("""
        SELECT SUM(r.monto_total) FROM reservas r
        JOIN lugares l ON r.lugar_id = l.id
        WHERE l.estacionamiento_id = ? AND r.estado = 'finalizada' AND r.fecha_fin LIKE ?
    """, (estacionamiento_id, f"{mes_str}%"))
    res_mes = cursor.fetchone()
    mes = res_mes[0] if res_mes and res_mes[0] else 0.0

    cursor.execute("""
        SELECT SUM(r.monto_total) FROM reservas r
        JOIN lugares l ON r.lugar_id = l.id
        WHERE l.estacionamiento_id = ? AND r.estado = 'finalizada'
    """, (estacionamiento_id,))
    res_total = cursor.fetchone()
    total = res_total[0] if res_total and res_total[0] else 0.0

    conn.close()
    return {"hoy": hoy, "mes": mes, "total": total}

# 4. Lista detallada de cobros para la tabla del Admin
def obtener_historial_pagos(estacionamiento_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, u.nombre, l.numero, l.tipo_vehiculo, r.fecha_reserva, r.fecha_fin, r.monto_total
        FROM reservas r
        JOIN usuarios u ON r.usuario_id = u.id
        JOIN lugares l ON r.lugar_id = l.id
        WHERE l.estacionamiento_id = ? AND r.estado = 'finalizada'
        ORDER BY r.fecha_fin DESC
    """, (estacionamiento_id,))
    filas = cursor.fetchall()
    conn.close()
    return filas

#ENCRIPTACION

def encriptar_dato(texto):
    if not texto:
        return ""
    # Convierte el texto en un hash SHA-256 hexadecimal de 64 caracteres
    return hashlib.sha256(str(texto).encode('utf-8')).hexdigest()