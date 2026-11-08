"""Adapta uma tarefa injetada ao ciclo de vida de QThread."""

import logging
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from dlpdownloader.modelos.erros import Cancelado, ErroAplicacao, SubstituicaoRecusada

LOGGER = logging.getLogger(__name__)


class Trabalhador(QObject):
    """Executa tarefa bloqueante; widgets são responsabilidade do controlador."""

    progresso = pyqtSignal(object)
    substituicao_solicitada = pyqtSignal(object)
    resultado = pyqtSignal(object)
    falhou = pyqtSignal(str)
    cancelado = pyqtSignal()
    substituicao_recusada = pyqtSignal()
    finalizado = pyqtSignal()

    def __init__(self, tarefa, cancelamento: threading.Event):
        super().__init__()
        self.tarefa = tarefa
        self.cancelamento = cancelamento
        self._ultimo = 0
        self._etapa = None

    def _emitir_progresso(self, evento) -> None:
        agora = time.monotonic()
        chave = (evento.etapa, evento.faixa)
        if chave != self._etapa or agora - self._ultimo >= 0.1 or evento.percentual == 100:
            self._ultimo = agora
            self._etapa = chave
            self.progresso.emit(evento)

    def confirmar_substituicao(self) -> bool:
        """Aguarda a decisão da GUI sem bloquear seu loop de eventos."""
        resposta = {"evento": threading.Event(), "aceita": False}
        self.substituicao_solicitada.emit(resposta)
        while not resposta["evento"].wait(0.1):
            if self.cancelamento.is_set():
                raise Cancelado()
        return resposta["aceita"]

    @pyqtSlot()
    def executar(self) -> None:
        """Uma única saída terminal, seguida sempre por finalizado."""
        try:
            resultado = self.tarefa(self.cancelamento, self._emitir_progresso)
            if self.cancelamento.is_set():
                raise Cancelado()
            self.resultado.emit(resultado)
        except SubstituicaoRecusada:
            self.substituicao_recusada.emit()
        except Cancelado:
            self.cancelado.emit()
        except ErroAplicacao as erro:
            LOGGER.warning("Tarefa interrompida: %s", type(erro).__name__)
            self.falhou.emit(str(erro))
        except Exception:
            LOGGER.exception("Erro inesperado no trabalhador")
            self.falhou.emit("Ocorreu uma falha inesperada. Consulte o arquivo de log.")
        finally:
            self.finalizado.emit()
