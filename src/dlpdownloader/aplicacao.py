"""Raiz de composição: instancia dependências, configura logs e inicia a GUI."""

import logging
import sys
from logging.handlers import RotatingFileHandler

from PyQt6.QtCore import QStandardPaths, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from dlpdownloader.config.caminhos import caminho_icone, diretorio_dados, raiz_projeto
from dlpdownloader.controladores.download import ControladorDownload
from dlpdownloader.servicos.dependencias import verificar
from dlpdownloader.servicos.preferencias import Preferencias
from dlpdownloader.servicos.yt_dlp import ServicoDownload
from dlpdownloader.visoes.janela_principal import JanelaPrincipal
from dlpdownloader.visoes.tema import aplicar_tema


def main() -> int:
    """Inicia aplicação com recursos independentes do diretório de trabalho."""
    from pathlib import Path

    app = QApplication(sys.argv)
    app.setApplicationName("DLPDownloader")
    app.setWindowIcon(QIcon(str(caminho_icone())))
    aplicar_tema(app)
    dados = diretorio_dados()
    try:
        dados.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            dados / "aplicacao.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        logging.basicConfig(level=logging.INFO, handlers=[handler])
    except OSError:
        logging.basicConfig(level=logging.INFO)
    padrao = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation))
    janela = JanelaPrincipal(caminho_icone())
    preferencias = Preferencias(dados / "config.json", padrao)
    controlador = ControladorDownload(
        janela,
        preferencias,
        lambda cancelar: verificar(raiz_projeto(), cancelar),
        ServicoDownload,
    )
    janela.show()
    QTimer.singleShot(0, controlador.inicializar)
    return app.exec()
