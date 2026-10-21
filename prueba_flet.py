import flet as ft

def main(page: ft.Page):
    page.title = "AgrovisionIA - Login"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 600

    # Campos de texto para usuario y contraseña
    txt_usuario = ft.TextField(label="Correo o Usuario", width=300, prefix_icon=ft.icons.PERSON)
    txt_password = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK)
    txt_mensaje = ft.Text("", color=ft.colors.RED)

    # Función que se ejecuta al presionar el botón de Iniciar Sesión
    def iniciar_sesion(e):
        usuario = txt_usuario.value
        password = txt_password.value

        # Validación básica de prueba local (aquí después lo conectaremos a tu FastAPI)
        if usuario == "" or password == "":
            txt_mensaje.value = "Por favor completa todos los campos"
            page.update()
        elif usuario == "admin" and password == "1234":
            txt_mensaje.color = ft.colors.GREEN
            txt_mensaje.value = "¡Bienvenido a AgrovisionIA!"
            page.update()
            # Aquí más adelante haremos la transición a la pantalla principal
        else:
            txt_mensaje.color = ft.colors.RED
            txt_mensaje.value = "Credenciales incorrectas"
            page.update()

    btn_login = ft.ElevatedButton(
        text="Iniciar Sesión", 
        width=300, 
        on_click=iniciar_sesion,
        color=ft.colors.WHITE,
        bgcolor=ft.colors.GREEN_700
    )

    # Diseño visual de la tarjeta de inicio de sesión
    page.add(
        ft.Column(
            [
                ft.Text("🌱 AgrovisionIA", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_800),
                ft.Text("Inicia sesión para continuar", size=14, color=ft.colors.GREY_700),
                ft.Container(height=20),
                txt_usuario,
                txt_password,
                txt_mensaje,
                ft.Container(height=10),
                btn_login
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

ft.app(target=main)