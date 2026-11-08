"""Coordena consultas manuais e silenciosas sem interferir no download."""

import logging
import threading

from PyQt6.QtCore import QObject, Qt, QThread, QTimer
from PyQt6.QtWidgets import QApplication

from dlpdownloader.config.versao import DESENVOLVIMENTO
from dlpdownloader.controladores.trabalhador import Trabalhador
from dlpdownloader.modelos.atualizacoes import normalizar_versao
from dlpdownloader.modelos.erros import ErroAplicacao

LOGGER = logging.getLogger(__name__)


class ControladorAtualizacoes(QObject):
    def __init__(self, janela, consultar, ler_versao, abrir_url, eh_beta=lambda: False):
        super().__init__(janela)
        self.janela = janela
        self.consultar = consultar
        self.ler_versao = ler_versao
        self.abrir_url = abrir_url
        self.eh_beta = eh_beta
        self.thread = None
        self.pendente = None
        self.manual = False
        self.resultado = None
        self.erro = None
        janela.atualizacao_solicitada.connect(lambda: self.iniciar(True))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._mostrar_pendente)
        self.timer.start(200)

    def iniciar(self, manual=False):
        if self.thread is not None:
            return
        self.manual = manual
        self.resultado = self.erro = None
        self.cancelamento = threading.Event()
        self.janela.consultando_atualizacao = True
        self.janela.acao_atualizar.setEnabled(False)
        if manual:
            self.janela.mostrar_consulta(self.cancelamento.set)
        self.thread = QThread(self)
        self.trabalhador = Trabalhador(self._consultar, self.cancelamento)
        self.trabalhador.moveToThread(self.thread)
        self.thread.started.connect(self.trabalhador.executar)
        self.trabalhador.resultado.connect(self._resultado)
        self.trabalhador.falhou.connect(self._erro)
        self.trabalhador.finalizado.connect(self.thread.quit, Qt.ConnectionType.DirectConnection)
        self.trabalhador.finalizado.connect(self.trabalhador.deleteLater)
        self.thread.finished.connect(self._terminar)
        self.thread.start()

    def _consultar(self, cancelar, progresso):
        local = self.ler_versao()
        if local is None:
            raise ErroAplicacao(
                DESENVOLVIMENTO + ". Use uma distribuição compilada para verificar atualizações."
            )
        local_normalizada = normalizar_versao(local)
        remota, url = self.consultar()
        beta = self.eh_beta()
        disponivel = remota > local_normalizada or (beta and remota == local_normalizada)
        return disponivel, f"{local} (beta)" if beta else local, remota, url

    def _resultado(self, resultado):
        self.resultado = resultado

    def _erro(self, erro):
        self.erro = erro

    def _terminar(self):
        self.thread.wait()
        self.thread.deleteLater()
        self.thread = self.trabalhador = None
        self.janela.consultando_atualizacao = False
        self.janela.acao_atualizar.setEnabled(not self.janela._ocupada)
        self.janela.fechar_consulta()
        if self.cancelamento.is_set():
            return
        if self.erro:
            if self.manual:
                self.janela.exibir_erro(self.erro)
            else:
                LOGGER.warning("Consulta automática de atualização falhou.")
        elif self.resultado:
            if self.resultado[0]:
                self.pendente = self.resultado
                self._mostrar_pendente()
            elif self.manual:
                self.janela.informar_atualizado(self.resultado[1])

    def _mostrar_pendente(self):
        if (
            not self.pendente
            or self.janela._ocupada
            or QApplication.activeModalWidget() is not None
        ):
            return
        _, local, remota, url = self.pendente
        self.pendente = None
        if self.janela.oferecer_atualizacao(local, ".".join(map(str, remota))):
            if not self.abrir_url(url):
                self.janela.exibir_erro(
                    "Não foi possível abrir o navegador. Copie este link: " + url
                )

    def encerrar(self):
        """Adia o fechamento até a tarefa limitada por timeout liberar a thread."""
        self.pendente = None
        self.timer.stop()
        if self.thread is not None:
            self.cancelamento.set()
            self.thread.finished.connect(self.janela.close)
            return False
        return True
