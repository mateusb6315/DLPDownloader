import flet as ft
from dlp import Downloader
import ctypes


class Interface:
    def __init__(self, page: ft.Page):
        self.page = page
        self.url_input = ft.TextField(label="Link do vídeo", width=350)
        self.mp4_button = ft.ElevatedButton("Download MP4", on_click=self.download_mp4)
        self.m4a_button = ft.ElevatedButton("Download M4A", on_click=self.download_m4a)
        self.status_text = ft.Text("")

    def popup_windows(self, titulo, mensagem):
        ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 0x40)

    # def fechar_popup(self):
    #    self.popup.open = False
    #    self.page.update()

    # def abrir_popup(self, message):
    #    self.popup = ft.AlertDialog(
    #        title=ft.Text("Download Completo"),
    #        content=ft.Text(message),
    #        actions=[ft.ElevatedButton("OK", on_click=self.fechar_popup)],
    #    )
    #    self.page.overlay.append(self.popup)
    #    self.popup.open = True
    #    self.page.update()

    def download_mp4(self):
        url = self.url_input.value
        downloader = Downloader(url)
        downloader.downloadMP4()
        self.popup_windows("Download completo", "O vídeo foi baixado com sucesso!")

    def download_m4a(self):
        url = self.url_input.value
        downloader = Downloader(url)
        downloader.downloadM4A()
        self.popup_windows("Download completo", "O áudio foi baixado com sucesso!")
