"""Coordena as intenções da View e o ciclo de vida de uma operação por vez."""

import logging
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSlot

from dlpdownloader.config.interface import ETAPAS, TEXTOS
from dlpdownloader.controladores.formatacao import formatar_detalhes
from dlpdownloader.controladores.trabalhador import Trabalhador
from dlpdownloader.modelos.download import ATIVOS, Estado, SolicitacaoDownload, validar_transicao
from dlpdownloader.modelos.erros import ErroAplicacao
from dlpdownloader.servicos.arquivos import validar_destino

LOGGER = logging.getLogger(__name__)


class ControladorDownload(QObject):
    """Recebe serviços por injeção; mudanças de estado passam por _transicionar."""

    def __init__(self, janela, preferencias, verificar, criar_servico):
        super().__init__(janela)
        self.janela = janela
        self.preferencias = preferencias
        self.verificar = verificar
        self.criar_servico = criar_servico
        self.estado = Estado.VERIFICANDO
        self.servico = None
        self.thread = None
        self.trabalhador = None
        self.cancelamento = threading.Event()
        self._fechar = False
        self._terminal = None
        self._tipo_tarefa = "ambiente"
        janela.download_solicitado.connect(self.iniciar)
        janela.pasta_solicitada.connect(self.escolher_pasta)
        janela.fechamento_solicitado.connect(self.fechar)

    def inicializar(self) -> None:
        """Abre a GUI antes da verificação e leitura de preferências."""
        self._transicionar(Estado.VERIFICANDO)
        self._executar_tarefa(self._carregar_ambiente)

    def _carregar_ambiente(self, cancelar, progresso):
        preferencias = self.preferencias.carregar()
        try:
            ferramentas = self.verificar(cancelar)
            return preferencias, ferramentas, ""
        except ErroAplicacao as erro:
            return preferencias, None, str(erro)

    def _executar_tarefa(self, tarefa) -> None:
        self.cancelamento = threading.Event()
        self._terminal = None
        self.thread = QThread(self)
        self.trabalhador = Trabalhador(tarefa, self.cancelamento)
        self.trabalhador.moveToThread(self.thread)
        self.thread.started.connect(self.trabalhador.executar)
        self.trabalhador.progresso.connect(self._ao_progresso)
        self.trabalhador.resultado.connect(self._ao_resultado)
        self.trabalhador.falhou.connect(self._ao_erro)
        self.trabalhador.cancelado.connect(self._ao_cancelado)
        self.trabalhador.finalizado.connect(self.thread.quit, Qt.ConnectionType.DirectConnection)
        self.trabalhador.finalizado.connect(self.trabalhador.deleteLater)
        self.thread.finished.connect(self._finalizar_thread)
        self.thread.start()

    @pyqtSlot(str, str, object, str)
    def iniciar(self, url: str, perfil: str, bitrate: int | None, destino: str) -> None:
        """Ignora ações repetidas e valida antes de criar trabalho."""
        if self.estado != Estado.PRONTO or self.thread is not None:
            return
        pedido = SolicitacaoDownload(url, perfil, bitrate, Path(destino))
        try:
            pedido.validar()
        except ErroAplicacao as erro:
            self.janela.atualizar_status(str(erro))
            return
        self._tipo_tarefa = "download"
        self._transicionar(Estado.PREPARANDO)
        self.janela.exibir_progresso(self.cancelar)
        self._executar_tarefa(
            lambda cancelar, progresso: self.servico.baixar(pedido, cancelar, progresso)
        )

    @pyqtSlot()
    def escolher_pasta(self) -> None:
        """Cancela sem erro; valida e salva a seleção imediatamente."""
        if self.thread is not None:
            return
        escolha = self.janela.escolher_diretorio(self.janela.destino.text())
        if not escolha:
            return
        try:
            validar_destino(Path(escolha))
            self.preferencias.salvar(Path(escolha))
        except (ErroAplicacao, OSError) as erro:
            self.janela.exibir_erro(str(erro))
            return
        self.janela.definir_destino(escolha)
        self.janela.atualizar_status(TEXTOS["pronto"])

    @pyqtSlot(object)
    def _ao_progresso(self, evento) -> None:
        if self.estado not in ATIVOS or self.estado == Estado.CANCELANDO:
            return
        estado = Estado.FINALIZANDO if evento.etapa == "finalizando" else Estado.BAIXANDO
        self._transicionar(estado)
        etapa = ETAPAS.get(evento.etapa, ETAPAS["preparando"]).format(faixa=evento.faixa)
        self.janela.atualizar_progresso(
            etapa,
            evento.percentual if evento.percentual is not None else -1,
            formatar_detalhes(evento) if evento.etapa == "baixando" else "",
        )

    @pyqtSlot(object)
    def _ao_resultado(self, resultado) -> None:
        self._terminal = ("resultado", resultado)

    @pyqtSlot(str)
    def _ao_erro(self, mensagem: str) -> None:
        self._terminal = ("erro", mensagem)

    @pyqtSlot()
    def _ao_cancelado(self) -> None:
        self._terminal = ("cancelado", None)

    @pyqtSlot()
    def _finalizar_thread(self) -> None:
        self.thread.wait()
        self.thread.deleteLater()
        self.thread = None
        self.trabalhador = None
        self.janela.finalizar_progresso()
        if self._fechar:
            self.janela.permitir_fechamento()
            return
        tipo, valor = self._terminal or ("erro", "O trabalho terminou sem resultado.")
        if self._tipo_tarefa == "ambiente":
            self._finalizar_ambiente(tipo, valor)
            return
        if tipo == "resultado":
            self._transicionar(Estado.CONCLUIDO)
            self.janela.atualizar_status(TEXTOS["sucesso"].format(caminho=valor))
            self.janela.exibir_sucesso(str(valor))
        elif tipo == "erro":
            self._transicionar(Estado.FALHOU)
            self.janela.atualizar_status(valor)
            self.janela.exibir_erro(valor)
        else:
            self._transicionar(Estado.CANCELADO)
            self.janela.atualizar_status(TEXTOS["cancelado"])
        self._transicionar(Estado.PRONTO)

    def _finalizar_ambiente(self, tipo, valor) -> None:
        if tipo == "resultado":
            (destino, aviso), ferramentas, erro = valor
            self.janela.definir_destino(str(destino))
            if ferramentas is not None:
                self.servico = self.criar_servico(ferramentas)
                self._transicionar(Estado.PRONTO)
                self.janela.atualizar_status(aviso or TEXTOS["pronto"])
            else:
                self._transicionar(Estado.INDISPONIVEL)
                self.janela.atualizar_status(f"{TEXTOS['indisponivel']} {erro}")
        else:
            self._transicionar(Estado.INDISPONIVEL)
            self.janela.atualizar_status(TEXTOS["indisponivel"])

    def _transicionar(self, estado: Estado) -> None:
        validar_transicao(self.estado, estado)
        self.estado = estado
        LOGGER.info("Estado da aplicação: %s", estado.name)
        self.janela.definir_ocupada(
            estado in ATIVOS or estado == Estado.VERIFICANDO,
            disponivel=estado != Estado.INDISPONIVEL,
        )

    @pyqtSlot()
    def cancelar(self) -> None:
        """Event é observado pelo serviço mesmo com o loop Qt do trabalhador ocupado."""
        if self.thread is not None:
            self.cancelamento.set()
            self._transicionar(Estado.CANCELANDO)
            self.janela.definir_cancelando()

    @pyqtSlot()
    def fechar(self) -> None:
        """Adia fechamento até cleanup sem bloquear a GUI esperando o serviço."""
        if self.thread is None:
            self.janela.permitir_fechamento()
        elif self.estado == Estado.VERIFICANDO or self.janela.perguntar_fechamento():
            self._fechar = True
            self.cancelar()
