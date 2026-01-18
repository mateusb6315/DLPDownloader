import flet as ft
from dlp import Downloader
from yt_dlp.utils import DownloadError, ExtractorError
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

    def popup_erro_windows(self, titulo, mensagem):
        ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 0x10)

    def download_mp4(self):
        url = self.url_input.value
        downloader = Downloader(url)
        try:
            downloader.downloadMP4()
            self.popup_windows("Download completo", "O vídeo foi baixado com sucesso!")
        except ExtractorError:
            self.popup_erro_windows("Erro", "Link inválido ou ausente")
        except DownloadError:
            self.popup_erro_windows("Erro", "Falha no download")

    def download_m4a(self):
        url = self.url_input.value
        downloader = Downloader(url)
        try:
            downloader.downloadM4A()
            self.popup_windows("Download completo", "O áudio foi baixado com sucesso!")
        except ExtractorError:
            self.popup_erro_windows("Erro", "Link inválido ou ausente")
        except DownloadError:
            self.popup_erro_windows("Erro", "Falha no download")
