import flet as ft


def vista_admin(page: ft.Page, db, sesion, mostrar_snack, cerrar_sesion):
    numero_field = ft.TextField(label="Número de lugar", width=150)
    tipo_dropdown = ft.Dropdown(
        label="Tipo de vehículo",
        width=180,
        options=[
            ft.DropdownOption("auto", "auto"),
            ft.DropdownOption("moto", "moto"),
            ft.DropdownOption("camioneta", "camioneta"),
        ],
    )
    precio_field = ft.TextField(label="Precio por hora", width=150)
    editando_id = {"id": None}

    tabla_lugares = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    tabla_pagos = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    # Módulo de métricas financieras
    txt_hoy = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    txt_mes = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
    txt_total = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700)

    def actualizar_recaudacion():
        try:
            resumen = db.obtener_resumen_recaudacion(sesion["estacionamiento_id"])
            txt_hoy.value = f"${resumen['hoy']:.2f}"
            txt_mes.value = f"${resumen['mes']:.2f}"
            txt_total.value = f"${resumen['total']:.2f}"
        except Exception:
            pass

    def cargar_historial_pagos():
        tabla_pagos.controls.clear()
        try:
            pagos = db.obtener_historial_pagos(sesion["estacionamiento_id"])
            if not pagos:
                tabla_pagos.controls.append(ft.Text("No hay cobros registrados aún.", color=ft.Colors.GREY_500))
            for p in pagos:
                # p -> (id, cliente, lugar_num, tipo, fecha_inicio, fecha_fin, monto)
                tabla_pagos.controls.append(
                    ft.Container(
                        padding=10,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                        bgcolor=ft.Colors.GREY_50,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(f"Cliente: {p[1]} — Lugar #{p[2]} ({p[3]})", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Salida: {p[5]}", size=12, color=ft.Colors.GREY_600),
                                    ]
                                ),
                                ft.Text(f"+${p[6]:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                            ],
                        ),
                    )
                )
        except Exception:
            tabla_pagos.controls.append(ft.Text("Error al cargar el historial de pagos.", color=ft.Colors.RED_400))

    def limpiar_formulario():
        editando_id["id"] = None
        numero_field.value = ""
        tipo_dropdown.value = None
        precio_field.value = ""
        page.update()

    def cargar_lugares():
        tabla_lugares.controls.clear()
        try:
            lugares = db.obtener_lugares(sesion["estacionamiento_id"])
            if not lugares:
                tabla_lugares.controls.append(ft.Text("No hay lugares cargados todavía.", color=ft.Colors.GREY_500))
            for lugar in lugares:
                tabla_lugares.controls.append(fila_lugar(lugar))
        except Exception:
            tabla_lugares.controls.append(ft.Text("Error al cargar los lugares.", color=ft.Colors.RED_400))
        page.update()

    def fila_lugar(lugar):
        estado_chip = ft.Container(
            content=ft.Text("Disponible" if lugar["disponible"] else "Ocupado", size=12, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_500 if lugar["disponible"] else ft.Colors.RED_400,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
        )
        return ft.Container(
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(f"Lugar #{lugar['numero']}  —  {lugar['tipo_vehiculo']}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"${lugar['precio_hora']:.2f} / hora", size=12, color=ft.Colors.GREY_600),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            estado_chip,
                            ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=lambda e, l=lugar: cargar_para_editar(l)),
                            ft.IconButton(icon=ft.Icons.DELETE, tooltip="Borrar", icon_color=ft.Colors.RED_400, on_click=lambda e, l=lugar: eliminar(l)),
                        ]
                    ),
                ],
            ),
        )

    def cargar_para_editar(lugar):
        editando_id["id"] = lugar["id"]
        numero_field.value = str(lugar["numero"])
        tipo_dropdown.value = lugar["tipo_vehiculo"]
        precio_field.value = str(lugar["precio_hora"])
        page.update()

    def eliminar(lugar):
        try:
            db.borrar_lugar(lugar["id"])
            mostrar_snack(f"Lugar #{lugar['numero']} eliminado")
            cargar_lugares()
        except Exception:
            mostrar_snack("Error al eliminar el lugar.", error=True)

    def guardar(e):
        if not numero_field.value or not tipo_dropdown.value or not precio_field.value:
            mostrar_snack("Completá número, tipo y precio", error=True)
            return
        try:
            numero = int(numero_field.value)
            precio = float(precio_field.value)
        except ValueError:
            mostrar_snack("Número y precio deben ser numéricos", error=True)
            return

        try:
            if editando_id["id"] is None:
                ok, msg = db.agregar_lugar(numero, tipo_dropdown.value, precio, sesion["estacionamiento_id"])
            else:
                ok, msg = db.modificar_lugar(editando_id["id"], numero, tipo_dropdown.value, precio, True)

            mostrar_snack(msg, error=not ok)
            if ok:
                limpiar_formulario()
                cargar_lugares()
        except Exception:
            mostrar_snack("Error al procesar la solicitud en la base de datos.", error=True)

    # Cargas iniciales
    cargar_lugares()
    actualizar_recaudacion()
    cargar_historial_pagos()

    try:
        estacionamiento_actual = db.obtener_estacionamiento_por_id(sesion["estacionamiento_id"])
        nombre_est = estacionamiento_actual['nombre']
    except Exception:
        nombre_est = "Estacionamiento"

    # Tarjeta resumen de cobros
    panel_recaudacion = ft.Container(
        padding=15,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=10,
        content=ft.Column(
            controls=[
                ft.Text("Resumen de Recaudación", size=16, weight=ft.FontWeight.BOLD),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    controls=[
                        ft.Column(controls=[ft.Text("Hoy", size=12, color=ft.Colors.GREY_600), txt_hoy]),
                        ft.Column(controls=[ft.Text("Este Mes", size=12, color=ft.Colors.GREY_600), txt_mes]),
                        ft.Column(controls=[ft.Text("Total Histórico", size=12, color=ft.Colors.GREY_600), txt_total]),
                    ],
                ),
            ]
        ),
    )

    return ft.View(
        route="/admin",
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.AppBar(
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Volver a estacionamientos",
                    on_click=lambda e: page.navigate("/estacionamientos"),
                ),
                title=ft.Text(f"Admin — {nombre_est}"),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
            ),
            ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        panel_recaudacion,
                        ft.Divider(),
                        ft.Text("Gestionar lugares", size=18, weight=ft.FontWeight.BOLD),
                        ft.ResponsiveRow(
                            controls=[
                                ft.Container(numero_field, col=3),
                                ft.Container(tipo_dropdown, col=3),
                                ft.Container(precio_field, col=3),
                                ft.Container(
                                    ft.Button("Guardar", icon=ft.Icons.SAVE, on_click=guardar),
                                    col=3,
                                ),
                            ]
                        ),
                        ft.TextButton("Cancelar edición", on_click=lambda e: limpiar_formulario()),
                        ft.Divider(),
                        ft.Text("Lugares cargados", size=18, weight=ft.FontWeight.BOLD),
                        tabla_lugares,
                        ft.Divider(),
                        ft.Text("Historial de Pagos y Salidas", size=18, weight=ft.FontWeight.BOLD),
                        tabla_pagos,
                    ]
                ),
            ),
        ],
    )
