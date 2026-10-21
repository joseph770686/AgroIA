import flet as ft

def main(page: ft.Page):
    page.title = "Prueba AgrovisionIA"
    page.add(ft.Text("¡Flet está funcionando correctamente!", size=20))

ft.app(target=main)