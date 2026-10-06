import flet as ft


def vista_conductor(page: ft.Page, db, sesion, mostrar_snack, cerrar_sesion):
    lista_lugares = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    lista_reservas = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    # 1. Creamos el Dropdown SIN 'on_change' dentro para evitar el crash de __init__
    tipo_filtro = ft.Dropdown(
        label="Filtrar por tipo de vehículo",
        width=250,
        options=[
            ft.DropdownOption("todos", "todos"),
            ft.DropdownOption("auto", "auto"),
            ft.DropdownOption("moto", "moto"),
            ft.DropdownOption("camioneta", "camioneta"),
        ],
        value="todos",
    )

    # 2. Función de carga y filtrado de disponibilidad
    # Función de carga y filtrado de disponibilidad
    def cargar_disponibles(e=None):
        lista_lugares.controls.clear()

        # Leemos directamente el valor seleccionado en el Dropdown tipo_filtro
        valor_str = str(tipo_filtro.value).strip().lower() if tipo_filtro.value else "todos"

        try:
            lugares = db.obtener_lugares(sesion["estacionamiento_id"], solo_disponibles=True)

            if valor_str != "todos":
                lugares_filtrados = []
                for l in lugares:
                    dict_l = dict(l)
                    tipo_v = str(dict_l.get("tipo_vehiculo", "")).strip().lower()
                    if tipo_v == valor_str:
                        lugares_filtrados.append(l)
                lugares = lugares_filtrados

            if not lugares:
                lista_lugares.controls.append(
                    ft.Text("No hay lugares disponibles con ese filtro.", color=ft.Colors.GREY_500)
                )
            else:
                for lugar in lugares:
                    lista_lugares.controls.append(fila_disponible(lugar))
        except Exception:
            lista_lugares.controls.append(
                ft.Text("Error al cargar disponibilidad.", color=ft.Colors.RED_400)
            )

        page.update()

    # Enlace externo de evento
    tipo_filtro.on_change = cargar_disponibles

    def finalizar_y_cobrar(reserva_id):
        try:
            ok, msg = db.finalizar_reserva_y_cobrar(reserva_id)
            mostrar_snack(msg, error=not ok)
            cargar_disponibles()
            cargar_mis_reservas()
        except Exception:
            mostrar_snack("Error al finalizar la estadía.", error=True)

    def fila_disponible(lugar):
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
                    ft.Button(
                        "Reservar",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=lambda e, l=lugar: reservar(l),
                    ),
                ],
            ),
        )

    def reservar(lugar):
        try:
            ok, msg = db.reservar_lugar(lugar["id"], sesion["usuario"]["id"])
            mostrar_snack(msg, error=not ok)
            cargar_disponibles()
            cargar_mis_reservas()
        except Exception:
            mostrar_snack("Error procesando la reserva.", error=True)

    def cargar_mis_reservas(e=None):
        lista_reservas.controls.clear()
        try:
            reservas = db.obtener_reservas_usuario(sesion["usuario"]["id"])
            if not reservas:
                lista_reservas.controls.append(ft.Text("Todavía no hiciste ninguna reserva.", color=ft.Colors.GREY_500))
            else:
                for r in reservas:
                    lista_reservas.controls.append(fila_reserva(r))
        except Exception as ex:
            lista_reservas.controls.append(ft.Text(f"Error cargando el historial: {ex}", color=ft.Colors.RED_400))
        page.update()

    def fila_reserva(r):
        dict_r = dict(r) if not isinstance(r, dict) else r
        estado = str(dict_r.get("estado", "")).lower()

        color_estado = {
            "activa": ft.Colors.GREEN_500,
            "finalizada": ft.Colors.BLUE_600,
            "cancelada": ft.Colors.RED_400,
        }.get(estado, ft.Colors.GREY_500)

        acciones = []
        if estado == "activa":
            acciones.extend([
                ft.Button(
                    "Finalizar y Pagar",
                    icon=ft.Icons.ATTACH_MONEY,
                    on_click=lambda e, rid=dict_r["id"]: finalizar_y_cobrar(rid),
                ),
                ft.TextButton("Cancelar", icon=ft.Icons.CANCEL, on_click=lambda e, rid=dict_r["id"]: cancelar(rid)),
            ])

        monto = dict_r.get("monto_total", 0.0)
        info_monto = f" — Total cobrado: ${float(monto):.2f}" if estado == "finalizada" and monto else ""

        return ft.Container(
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(f"Lugar #{dict_r.get('numero', '')} — {dict_r.get('tipo_vehiculo', '')}", weight=ft.FontWeight.BOLD),
                            ft.Text(dict_r.get("estacionamiento_nombre", ""), size=12, color=ft.Colors.BLUE_600),
                            ft.Text(f"Inicio: {dict_r.get('fecha_reserva', '')}{info_monto}", size=12, color=ft.Colors.GREY_600),
                        ]
                    ),
                    ft.Row(controls=[ft.Text(estado.capitalize(), color=color_estado), *acciones]),
                ],
            ),
        )

    def cancelar(reserva_id):
        try:
            ok, msg = db.cancelar_reserva(reserva_id)
            mostrar_snack(msg, error=not ok)
            cargar_disponibles()
            cargar_mis_reservas()
        except Exception:
            mostrar_snack("Error al cancelar la reserva.", error=True)

    cargar_disponibles()
    cargar_mis_reservas()

    try:
        estacionamiento_actual = db.obtener_estacionamiento_por_id(sesion["estacionamiento_id"])
        nombre_est = estacionamiento_actual['nombre']
    except Exception:
        nombre_est = "Estacionamiento"

    return ft.View(
        route="/conductor",
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.AppBar(
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Volver a estacionamientos",
                    on_click=lambda e: page.navigate("/estacionamientos"),
                ),
                title=ft.Text(f"{nombre_est} — {sesion['usuario']['nombre']}"),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
            ),
            ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Buscar lugares disponibles", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                tipo_filtro,
                                ft.Button("Filtrar", icon=ft.Icons.FILTER_ALT, on_click=cargar_disponibles)
                            ]
                        ),
                        lista_lugares,
                        ft.Divider(),
                        ft.Text("Mis reservas", size=18, weight=ft.FontWeight.BOLD),
                        lista_reservas,
                    ]
                ),
            ),
        ],
    )
