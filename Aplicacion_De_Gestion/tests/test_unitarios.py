import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import database as db


@pytest.fixture
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_NAME", str(tmp_path / "test_estacionamiento.db"))
    db.init_db()
    db.preparar_tabla_usuarios()
    db.preparar_tabla_facturacion()
    return db


def crear_lugar_y_usuario(database, precio_hora=1000):
    database.agregar_estacionamiento("Estacionamiento de prueba", "Dirección de prueba")
    conexion = database.get_connection()
    estacionamiento = conexion.execute(
        "SELECT id FROM estacionamientos WHERE nombre = ?",
        ("Estacionamiento de prueba",),
    ).fetchone()
    conexion.close()

    database.crear_usuario("conductor_prueba", "clave_segura", "Conductor de prueba", "conductor")
    conexion = database.get_connection()
    usuario = conexion.execute(
        "SELECT id FROM usuarios WHERE username = ?",
        ("conductor_prueba",),
    ).fetchone()
    conexion.close()

    database.agregar_lugar(1, "auto", precio_hora, estacionamiento["id"])
    lugar = database.obtener_lugares(estacionamiento["id"])[0]
    return estacionamiento["id"], usuario["id"], lugar["id"]



def test_registrar_usuario_valida_datos_y_permite_login(base_temporal):
    ok, mensaje = base_temporal.registrar_usuario(
        "  Ana Pérez  ",
        "  ana  ",
        "clave_segura",
        "ana@example.com",
        "12345678",
    )

    assert ok is True
    assert mensaje == "Registro exitoso. Ahora podés iniciar sesión."
    usuario = base_temporal.validar_login("ANA", "clave_segura")
    assert usuario is not None
    assert usuario["nombre"] == "Ana Pérez"


@pytest.mark.parametrize(
    ("nombre", "usuario", "clave", "email", "dni", "mensaje"),
    [
        ("Ana", "ana", "clave_segura", "ana@example.com", "12345678", None),
        ("Ana", "ana", "corta", "ana@example.com", "12345678",
         "La contraseña debe tener al menos 8 caracteres."),
        ("Ana", "ana", "clave_segura", "ana@example.com", "1234",
         "El DNI debe tener exactamente 8 dígitos numéricos."),
        ("", "ana", "clave_segura", "ana@example.com", "12345678",
         "Todos los campos son obligatorios."),
    ],
)
def test_registrar_usuario_rechaza_datos_invalidos(
    base_temporal, nombre, usuario, clave, email, dni, mensaje
):
    ok, resultado = base_temporal.registrar_usuario(nombre, usuario, clave, email, dni)

    if mensaje is None:
        assert ok is True
    else:
        assert ok is False
        assert resultado == mensaje


def test_agregar_lugar_rechaza_numero_duplicado(base_temporal):
    base_temporal.agregar_estacionamiento("Prueba", "Dirección")
    conexion = base_temporal.get_connection()
    estacionamiento = conexion.execute(
        "SELECT id FROM estacionamientos WHERE nombre = ?",
        ("Prueba",),
    ).fetchone()
    conexion.close()

    assert base_temporal.agregar_lugar(1, "auto", 1000, estacionamiento["id"])[0] is True
    assert base_temporal.agregar_lugar(1, "moto", 500, estacionamiento["id"]) == (
        False,
        "Ya existe un lugar con ese número en este estacionamiento",
    )


def test_reservar_lugar_y_cancelar_libera_lugar(base_temporal):
    estacionamiento_id, usuario_id, lugar_id = crear_lugar_y_usuario(base_temporal)

    assert base_temporal.reservar_lugar(lugar_id, usuario_id)[0] is True
    assert base_temporal.reservar_lugar(lugar_id, usuario_id) == (
        False,
        "El lugar ya no está disponible",
    )
    assert base_temporal.contar_lugares(estacionamiento_id) == (1, 0)

    conexion = base_temporal.get_connection()
    reserva = conexion.execute("SELECT id FROM reservas WHERE lugar_id = ?", (lugar_id,)).fetchone()
    conexion.close()

    assert base_temporal.cancelar_reserva(reserva["id"])[0] is True
    assert base_temporal.contar_lugares(estacionamiento_id) == (1, 1)


def test_finalizar_reserva_calcula_cobro_y_libera_lugar(base_temporal):
    estacionamiento_id, usuario_id, lugar_id = crear_lugar_y_usuario(base_temporal, precio_hora=750)
    base_temporal.reservar_lugar(lugar_id, usuario_id)

    conexion = base_temporal.get_connection()
    reserva = conexion.execute("SELECT id FROM reservas WHERE lugar_id = ?", (lugar_id,)).fetchone()
    inicio = (datetime.now() - timedelta(minutes=61)).strftime("%Y-%m-%d %H:%M:%S")
    conexion.execute("UPDATE reservas SET fecha_reserva = ? WHERE id = ?", (inicio, reserva["id"]))
    conexion.commit()
    conexion.close()

    ok, mensaje = base_temporal.finalizar_reserva_y_cobrar(reserva["id"])

    assert ok is True
    assert "Total a pagar: $1500.00" in mensaje
    assert base_temporal.contar_lugares(estacionamiento_id) == (1, 1)

    conexion = base_temporal.get_connection()
    reserva_finalizada = conexion.execute(
        "SELECT estado, monto_total, fecha_fin FROM reservas WHERE id = ?",
        (reserva["id"],),
    ).fetchone()
    conexion.close()
    assert reserva_finalizada["estado"] == "finalizada"
    assert reserva_finalizada["monto_total"] == 1500
    assert reserva_finalizada["fecha_fin"] is not None
