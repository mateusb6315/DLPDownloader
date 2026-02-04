from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
)
from dlp import Downloader
from yt_dlp.utils import DownloadError, ExtractorError
import ctypes


class Interface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DLP Downloader")
        self.setFixedSize(500, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.addStretch()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Link:")
        self.url_input.setFixedWidth(350)
        layout.addWidget(self.url_input)
        layout.setContentsMargins(75, 0, 75, 0)

        button_layout = QHBoxLayout()
        self.mp4_button = QPushButton("MP4")
        self.m4a_button = QPushButton("M4A")
        self.mp3_button = QPushButton("MP3")
        self.mp4_button.clicked.connect(self.download_mp4)
        self.m4a_button.clicked.connect(self.download_m4a)
        self.mp3_button.clicked.connect(self.download_mp3)
        button_layout.addWidget(self.mp4_button)
        button_layout.addWidget(self.m4a_button)
        button_layout.addWidget(self.mp3_button)
        layout.addLayout(button_layout)

        self.status_text = QLabel("")
        layout.addWidget(self.status_text)

        layout.addStretch()
        central_widget.setLayout(layout)

    def popup_windows(self, titulo, mensagem):
        ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 0x40)

    def popup_erro_windows(self, titulo, mensagem):
        ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 0x10)

    def download_mp4(self):
        url = self.url_input.text()
        downloader = Downloader(url)
        try:
            downloader.downloadMP4()
            self.popup_windows("Download completo", "O vídeo foi baixado com sucesso!")
        except ExtractorError:
            self.popup_erro_windows("Erro", "Link inválido ou ausente")
        except DownloadError:
            self.popup_erro_windows("Erro", "Falha no download")

    def download_m4a(self):
        url = self.url_input.text()
        downloader = Downloader(url)
        try:
            downloader.downloadM4A()
            self.popup_windows("Download completo", "O áudio foi baixado com sucesso!")
        except ExtractorError:
            self.popup_erro_windows("Erro", "Link inválido ou ausente")
        except DownloadError:
            self.popup_erro_windows("Erro", "Falha no download")

    def download_mp3(self):
        url = self.url_input.text()
        downloader = Downloader(url)
        try:
            downloader.downloadMP3()
            self.popup_windows("Download completo", "O áudio foi baixado com sucesso!")
        except ExtractorError:
            self.popup_erro_windows("Erro", "Link inválido ou ausente")
        except DownloadError:
            self.popup_erro_windows("Erro", "Falha no download")
