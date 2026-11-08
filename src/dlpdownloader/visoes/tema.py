"""Aplica um tema claro e previsível em um único ponto."""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from dlpdownloader.config.interface import CORES, ESTILO


def aplicar_tema(app: QApplication) -> None:
    """Define estilo e paleta sem depender do tema do sistema operacional."""
    app.setStyle("Fusion")
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(CORES["fundo"]))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(CORES["texto"]))
    paleta.setColor(QPalette.ColorRole.Text, QColor(CORES["texto"]))
    paleta.setColor(QPalette.ColorRole.Base, QColor("white"))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(CORES["texto"]))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(CORES["destaque"]))
    app.setPalette(paleta)
    app.setStyleSheet(ESTILO)
