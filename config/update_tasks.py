"""Coordena a consulta de releases separadamente da operação de download."""

import logging
import threading

from PyQt6.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication

from config.worker import Trabalhador
from ui.text import ATUALIZACOES

LOGGER = logging.getLogger(__name__)


class ConsultaAtualizacoes(QObject):
    """Executa uma consulta por vez e apresenta seu resultado na GUI."""

    encerrada = pyqtSignal()

    def __init__(self, janela, consultar, abrir_release, pode_oferecer_automaticamente):
        super().__init__(janela)
        self.janela = janela
        self.consultar = consultar
        self.abrir_release = abrir_release
        self.pode_oferecer_automaticamente = pode_oferecer_automaticamente
        self._thread = None
        self._trabalhador = None
        self._cancelamento = threading.Event()
        self._encerrando = False
        self._manual = False
        self._resultado = None
        self._erro = ""
        self._oferta_automatica = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._apresentar)
        janela.definir_consulta_disponivel(True)
        janela.atualizacao_solicitada.connect(self.iniciar_manual)
        janela.cancelamento_consulta_solicitado.connect(self.cancelar)

    @pyqtSlot()
    def iniciar_manual(self) -> None:
        self.iniciar(manual=True)

    def iniciar(self, *, manual: bool = False) -> None:
        if self._thread is not None or self._encerrando:
            return
        self._timer.stop()
        self._manual = manual
        self._resultado = None
        self._erro = ""
        self._cancelamento = threading.Event()
        self.janela.definir_consulta_disponivel(False)
        if manual:
            self.janela.mostrar_consulta()
        self._thread = QThread(self)
        self._trabalhador = Trabalhador(
            lambda cancelar, _: self.consultar(cancelar), self._cancelamento
        )
        self._trabalhador.moveToThread(self._thread)
        self._thread.started.connect(self._trabalhador.executar)
        self._trabalhador.resultado.connect(self._receber_resultado)
        self._trabalhador.falhou.connect(self._receber_erro)
        self._trabalhador.finalizado.connect(self._thread.quit, Qt.ConnectionType.DirectConnection)
        self._trabalhador.finalizado.connect(self._trabalhador.deleteLater)
        self._thread.finished.connect(self._finalizar)
        self._thread.start()

    @pyqtSlot()
    def cancelar(self) -> None:
        self._cancelamento.set()

    def encerrar(self) -> bool:
        """Retorna se a janela já pode ser fechada."""
        self._encerrando = True
        self._timer.stop()
        self._oferta_automatica = None
        self.janela.definir_consulta_disponivel(False)
        self.janela.definir_consulta_cancelando()
        self.cancelar()
        return self._thread is None

    @pyqtSlot(object)
    def _receber_resultado(self, resultado) -> None:
        self._resultado = resultado

    @pyqtSlot(str)
    def _receber_erro(self, mensagem: str) -> None:
        self._erro = mensagem

    @pyqtSlot()
    def _finalizar(self) -> None:
        self._thread.wait()
        self._thread.deleteLater()
        self._thread = self._trabalhador = None
        self.janela.fechar_consulta()
        if self._encerrando:
            self.encerrada.emit()
            return
        self.janela.definir_consulta_disponivel(True)
        if self._cancelamento.is_set():
            self._resultado = None
            self._erro = ""
        elif not self._manual:
            if self._erro:
                LOGGER.warning("Consulta automática de atualização falhou.")
            if self._resultado and self._resultado.disponivel:
                self._oferta_automatica = self._resultado
            self._resultado = None
            self._erro = ""
        elif self._resultado is not None:
            self._oferta_automatica = None
        self._apresentar()

    @pyqtSlot()
    def _apresentar(self) -> None:
        if self._encerrando or self._thread is not None:
            return
        manual = self._resultado is not None or bool(self._erro)
        if not manual and self._oferta_automatica is None:
            return
        if QApplication.activeModalWidget() is not None or (
            not manual and not self.pode_oferecer_automaticamente()
        ):
            self._timer.start()
            return
        resultado, erro = self._resultado, self._erro
        self._resultado = None
        self._erro = ""
        if not manual:
            oferta = self._oferta_automatica
            self._oferta_automatica = None
            self._oferecer(oferta)
        elif erro:
            self.janela.exibir_erro(erro)
            if self._oferta_automatica is not None:
                self._timer.start()
        elif resultado and resultado.disponivel:
            self._oferecer(resultado)
        elif resultado:
            self.janela.informar_atualizado(resultado.versao_atual)

    def _oferecer(self, resultado) -> None:
        release = resultado.disponivel
        aceitou = self.janela.oferecer_atualizacao(resultado.versao_atual, release.versao)
        if aceitou and not self._encerrando and not self.abrir_release(release.url):
            self.janela.exibir_erro(ATUALIZACOES["erro_navegador"].format(url=release.url))
