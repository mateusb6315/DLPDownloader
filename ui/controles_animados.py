"""Controles com transições visuais para a janela principal."""

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QComboBox, QPushButton, QStyle, QStyleOptionButton, QStylePainter


class SelecaoAnimada(QComboBox):
    """Suaviza o realce da borda ao entrar, sair ou receber foco."""

    def __init__(self):
        super().__init__()
        self._realce = 0.0
        self._animacao = QPropertyAnimation(self, b"realce", self)
        self._animacao.setDuration(150)
        self._animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._aplicar_cor()

    def _obter_realce(self):
        return self._realce

    def _definir_realce(self, valor):
        self._realce = valor
        self._aplicar_cor()

    realce = pyqtProperty(float, _obter_realce, _definir_realce)

    def _aplicar_cor(self):
        inicio, fim = QColor("#bcc7d8"), QColor("#245dcc")
        cor = QColor(
            *[
                round(a + (b - a) * self._realce)
                for a, b in zip(inicio.getRgb()[:3], fim.getRgb()[:3], strict=True)
            ]
        )
        self.setStyleSheet(f"QComboBox {{ border: 1px solid {cor.name()}; }}")

    def _animar(self):
        self._animacao.stop()
        self._animacao.setStartValue(self._realce)
        self._animacao.setEndValue(
            1.0 if self.isEnabled() and (self.underMouse() or self.hasFocus()) else 0.0
        )
        self._animacao.start()

    def enterEvent(self, evento):
        super().enterEvent(evento)
        self._animar()

    def leaveEvent(self, evento):
        super().leaveEvent(evento)
        self._animar()

    def focusInEvent(self, evento):
        super().focusInEvent(evento)
        self._animar()

    def focusOutEvent(self, evento):
        super().focusOutEvent(evento)
        self._animar()


class BotaoAnimado(QPushButton):
    """Reduz apenas a pintura, preservando geometria e área de clique."""

    def __init__(self, texto):
        super().__init__(texto)
        self._escala = 1.0
        self._animacao = QPropertyAnimation(self, b"escala", self)
        self._animacao.setDuration(100)
        self._animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pressionado = False
        self._animacao.finished.connect(self._concluir_animacao)
        self.pressed.connect(self._pressionar)
        self.released.connect(self._soltar)

    def _obter_escala(self):
        return self._escala

    def _definir_escala(self, valor):
        self._escala = valor
        self.update()

    escala = pyqtProperty(float, _obter_escala, _definir_escala)

    def _pressionar(self):
        self._pressionado = True
        self._animar(0.95)

    def _soltar(self):
        self._pressionado = False
        if self._escala <= 0.951:
            self._animar(1.0)
        else:
            self._animar(0.95)

    def _concluir_animacao(self):
        if not self._pressionado and self._escala < 1.0:
            self._animar(1.0)

    def _animar(self, destino):
        self._animacao.stop()
        self._animacao.setStartValue(self._escala)
        self._animacao.setEndValue(destino)
        self._animacao.start()

    def paintEvent(self, evento):
        painter = QStylePainter(self)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._escala, self._escala)
        painter.translate(-self.width() / 2, -self.height() / 2)
        opcao = QStyleOptionButton()
        self.initStyleOption(opcao)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, opcao)
