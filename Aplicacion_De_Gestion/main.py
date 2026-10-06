import flet as ft
import database as db
from views import (
    vista_admin,
    vista_conductor,
    vista_estacionamientos,
    vista_login,
    vista_registro,
)


def main(page: ft.Page):
    page.title = "ParkingSeach"
    page.window.width = 900
    page.window.height = 650
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    try:
        db.init_db()
        db.preparar_tabla_facturacion()
        db.preparar_tabla_usuarios()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

    # Guardamos el usuario logueado y el estacionamiento elegido, accesibles desde cualquier vista
    sesion = {"usuario": None, "estacionamiento_id": None}

    # Utilidades de UI
    def mostrar_snack(mensaje, error=False):
        snack = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
            open=True,
        )
        page.snack_bar = snack
        try:
            page.overlay.append(snack)
        except Exception:
            pass
        page.update()
        
        
    def cerrar_sesion(e=None):
        sesion["usuario"] = None
        sesion["estacionamiento_id"] = None
        page.navigate("/login")

    def route_change(e):
        page.views.clear()
        ruta = page.route

        if ruta == "/registro":
            page.views.append(vista_registro(page, db, sesion, mostrar_snack, cerrar_sesion))
        elif sesion["usuario"] is None:
            page.views.append(vista_login(page, db, sesion, mostrar_snack, cerrar_sesion))
        elif ruta == "/estacionamientos":
            page.views.append(vista_estacionamientos(page, db, sesion, mostrar_snack, cerrar_sesion))
        elif ruta == "/admin" and sesion["usuario"].get("rol") == "admin" and sesion["estacionamiento_id"] is not None:
            page.views.append(vista_admin(page, db, sesion, mostrar_snack, cerrar_sesion))
        elif ruta == "/conductor" and sesion["usuario"].get("rol") == "conductor" and sesion["estacionamiento_id"] is not None:
            page.views.append(vista_conductor(page, db, sesion, mostrar_snack, cerrar_sesion))
        else:
            page.views.append(vista_estacionamientos(page, db, sesion, mostrar_snack, cerrar_sesion))

        page.update()

    page.on_route_change = route_change

    if page.route == "/":
        page.route = "/login"
    route_change(None)


if __name__ == "__main__":
    ft.run(main)
