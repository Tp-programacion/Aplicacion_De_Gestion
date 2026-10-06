import flet as ft


def vista_login(page: ft.Page, db, sesion, mostrar_snack, cerrar_sesion):
    username_field = ft.TextField(label="Usuario", width=300, autofocus=True)
    password_field = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True)

    def hacer_login(e):
        try:
            usuario = db.validar_login(username_field.value.strip(), password_field.value)
            if usuario is None:
                mostrar_snack("Usuario o contraseña incorrectos", error=True)
                return

            # MEJORA: Seguridad. Purgamos la contraseña antes de guardar en memoria de sesión
            usuario_seguro = dict(usuario)
            usuario_seguro.pop("password", None)

            sesion["usuario"] = usuario_seguro
            page.navigate("/estacionamientos")
        except Exception as ex:
            mostrar_snack("Error de conexión con la base de datos.", error=True)

    def ir_a_registro(e):
        page.navigate("/registro")

    return ft.View(
        route="/login",
        controls=[
            ft.Container(
                alignment=ft.Alignment.CENTER,
                expand=True,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.LOCAL_PARKING, size=60, color=ft.Colors.BLUE_600),
                        ft.Text("ParkingSeach", size=26, weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        username_field,
                        password_field,
                        ft.Container(height=10),
                        ft.Button("Ingresar", width=300, on_click=hacer_login),
                        ft.TextButton("Crear cuenta de conductor", on_click=ir_a_registro),
                        ft.Container(height=10),
                        ft.Text(
                            "Admin por defecto -> usuario: admin | contraseña: admin123",
                            size=11,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                ),
            )
        ],
    )


# VISTA: REGISTRO (solo crea usuarios tipo conductor)
# VISTA: REGISTRO DE USUARIOS


def vista_registro(page: ft.Page, db, sesion, mostrar_snack, cerrar_sesion):
    nombre_field = ft.TextField(label="Nombre completo", width=300)
    usuario_field = ft.TextField(label="Nombre de usuario", width=300)
    email_field = ft.TextField(label="Correo electrónico (Email)", width=300)
    dni_field = ft.TextField(
        label="DNI (8 dígitos)",
        width=300,
        max_length=8,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    clave_field = ft.TextField(label="Contraseña (mínimo 8 caracteres)", password=True, can_reveal_password=True, width=300)

    def procesar_registro(e):
        ok, msg = db.registrar_usuario(
            nombre=nombre_field.value,
            usuario=usuario_field.value,
            clave=clave_field.value,
            email=email_field.value,
            dni=dni_field.value,
            rol="conductor"
        )
        mostrar_snack(msg, error=not ok)
        if ok:
            page.navigate("/login")

    return ft.View(
        route="/registro",
        controls=[
            ft.Container(
                alignment=ft.Alignment(0, 0),  # Centrado universal compatible con todas las versiones
                expand=True,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    controls=[
                        ft.Text("Crear nueva cuenta", size=24, weight=ft.FontWeight.BOLD),
                        nombre_field,
                        usuario_field,
                        email_field,
                        dni_field,
                        clave_field,
                        ft.Button("Registrarse", on_click=procesar_registro, width=300),
                        ft.TextButton("¿Ya tenés cuenta? Iniciá sesión", on_click=lambda e: page.navigate("/login")),
                    ],
                ),
            )
        ],
    )
