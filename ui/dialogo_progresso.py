"""Popup de acompanhamento sem conhecimento do serviço de download."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout

from ui.text import TEXTOS, TITULO


class DialogoProgresso(QDialog):
    """Exibe medições recebidas e emite intenção de cancelamento."""

    cancelamento_solicitado = pyqtSignal()

    def __init__(
        self, pai, texto_inicial=TEXTOS["progresso"], texto_cancelamento=TEXTOS["cancelando"]
    ):
        super().__init__(pai)
        self.setWindowTitle(TITULO)
        self.setWindowIcon(pai.windowIcon())
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumWidth(440)
        self._ativo = True
        self._texto_cancelamento = texto_cancelamento
        layout = QVBoxLayout(self)
        self.etapa = QLabel(texto_inicial)
        self.barra = QProgressBar()
        self.barra.setRange(0, 0)
        self.detalhes = QLabel("")
        self.cancelar = QPushButton(TEXTOS["cancelar"])
        self.cancelar.clicked.connect(self._solicitar_cancelamento)
        for widget in (self.etapa, self.barra, self.detalhes, self.cancelar):
            layout.addWidget(widget)

    def atualizar(self, etapa: str, percentual: int, detalhes: str) -> None:
        """Percentual negativo representa barra indeterminada."""
        self.etapa.setText(etapa)
        self.detalhes.setText(detalhes)
        self.barra.setRange(0, 0 if percentual < 0 else 100)
        self.barra.setFormat(TEXTOS["percentual"])
        if percentual >= 0:
            self.barra.setValue(percentual)

    def definir_cancelando(self) -> None:
        """Impede solicitações repetidas durante o encerramento."""
        self.cancelar.setEnabled(False)
        self.etapa.setText(self._texto_cancelamento)

    def finalizar(self) -> None:
        """Fecha o popup somente após o encerramento do trabalho."""
        self._ativo = False
        self.accept()

    def _solicitar_cancelamento(self) -> None:
        if self.cancelar.isEnabled():
            self.definir_cancelando()
            self.cancelamento_solicitado.emit()

    def reject(self) -> None:
        """Escape segue o mesmo cancelamento do botão e do X."""
        if self._ativo:
            self._solicitar_cancelamento()
        else:
            super().reject()

    def closeEvent(self, evento: QCloseEvent) -> None:
        if self._ativo:
            evento.ignore()
            self._solicitar_cancelamento()
        else:
            evento.accept()
