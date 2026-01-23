from interface import Interface
import flet as ft


def main(page: ft.Page):
    page.title = "DLP Downloader"
    page.window.width = 500
    page.window.height = 300
    page.window.resizable = False
    page.window.maximizable = False
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    interface = Interface(page)

    page.add(
        ft.Column(
            [
                interface.url_input,
                ft.Row(
                    [interface.mp4_button, interface.m4a_button, interface.mp3_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                interface.status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
    )


ft.app(target=main)
