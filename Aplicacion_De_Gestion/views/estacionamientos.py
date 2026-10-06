import flet as ft


def vista_estacionamientos(page: ft.Page, db, sesion, mostrar_snack, cerrar_sesion):
    lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def ir_a_estacionamiento(est):
        sesion["estacionamiento_id"] = est["id"]
        if sesion["usuario"]["rol"] == "admin":
            page.navigate("/admin")
        else:
            page.navigate("/conductor")

    def fila_estacionamiento(est):
        try:
            total, disponibles = db.contar_lugares(est["id"])
        except Exception:
            total, disponibles = 0, 0

        return ft.Container(
            padding=15,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            on_click=lambda e, est=est: ir_a_estacionamiento(est),
            ink=True,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(est["nombre"], size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(est["direccion"] or "Sin dirección cargada", size=12, color=ft.Colors.GREY_600),
                            ft.Text(
                                f"{disponibles} de {total} lugares disponibles",
                                size=12,
                                color=ft.Colors.GREEN_600 if disponibles > 0 else ft.Colors.RED_400,
                            ),
                        ]
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400),
                ],
            ),
        )

    def cargar_estacionamientos():
        lista.controls.clear()
        try:
            estacionamientos = db.obtener_estacionamientos()
            if not estacionamientos:
                lista.controls.append(ft.Text("No hay estacionamientos cargados todavía.", color=ft.Colors.GREY_500))
            for est in estacionamientos:
                lista.controls.append(fila_estacionamiento(est))
        except Exception:
            lista.controls.append(ft.Text("Error al cargar estacionamientos.", color=ft.Colors.RED_400))
        page.update()

    cargar_estacionamientos()

    return ft.View(
        route="/estacionamientos",
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.AppBar(
                title=ft.Text(f"Elegí un estacionamiento — {sesion['usuario']['nombre']}"),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
            ),
            ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Estacionamientos disponibles", size=18, weight=ft.FontWeight.BOLD),
                        lista,
                    ]
                ),
            ),
        ],
    )
