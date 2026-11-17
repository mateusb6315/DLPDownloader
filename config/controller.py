"""Coordena as intenções da View e o ciclo de vida de uma operação por vez."""

import logging
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSlot

from config.presentation import formatar_detalhes
from config.update_tasks import ConsultaAtualizacoes
from config.worker import Trabalhador
from services._models.download import ATIVOS, Estado, SolicitacaoDownload, validar_transicao
from services._models.erros import ErroAplicacao
from ui.text import ETAPAS, TEXTOS

LOGGER = logging.getLogger(__name__)


class ControladorDownload(QObject):
    """Recebe serviços por injeção; mudanças de estado passam por _transicionar."""

    def __init__(
        self,
        janela,
        *,
        carregar_preferencias,
        salvar_preferencias,
        validar_destino,
        verificar,
        criar_servico,
        reparo_disponivel=None,
        encerrar_tarefas=lambda: True,
        consultar_atualizacao=None,
        abrir_release=lambda _url: False,
    ):
        super().__init__(janela)
        self.janela = janela
        self.carregar_preferencias = carregar_preferencias
        self.salvar_preferencias = salvar_preferencias
        self.validar_destino = validar_destino
        self.verificar = verificar
        self.criar_servico = criar_servico
        self.reparo_disponivel = reparo_disponivel
        self.reparo_solicitado = False
        self.encerrar_tarefas = encerrar_tarefas
        self.estado = Estado.VERIFICANDO
        self.servico = None
        self.thread = None
        self.trabalhador = None
        self.cancelamento = threading.Event()
        self._fechar = False
        self._confirmando_fechamento = False
        self._substituicao_pendente = None
        self._terminal = None
        self._tipo_tarefa = "ambiente"
        self._atualizacoes = None
        if consultar_atualizacao is not None:
            self._atualizacoes = ConsultaAtualizacoes(
                janela,
                consultar_atualizacao,
                abrir_release,
                lambda: self.estado not in ATIVOS and self.estado != Estado.VERIFICANDO,
            )
            self._atualizacoes.encerrada.connect(self._concluir_fechamento)
        janela.download_solicitado.connect(self.iniciar)
        janela.pasta_solicitada.connect(self.escolher_pasta)
        janela.cancelamento_solicitado.connect(self.cancelar)
        janela.fechamento_solicitado.connect(self.fechar)
        janela.definir_ocupada(True)

    def inicializar(self) -> None:
        """Abre a GUI antes da verificação e leitura de preferências."""
        if self._fechar:
            return
        self._transicionar(Estado.VERIFICANDO)
        self._executar_tarefa(self._carregar_ambiente)
        if self._atualizacoes is not None:
            self._atualizacoes.iniciar()

    def _carregar_ambiente(self, cancelar, _progresso):
        preferencias = self.carregar_preferencias()
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
        self.trabalhador.substituicao_solicitada.connect(self._perguntar_substituicao)
        self.trabalhador.resultado.connect(self._ao_resultado)
        self.trabalhador.falhou.connect(self._ao_erro)
        self.trabalhador.cancelado.connect(self._ao_cancelado)
        self.trabalhador.substituicao_recusada.connect(self._ao_substituicao_recusada)
        self.trabalhador.finalizado.connect(self.thread.quit, Qt.ConnectionType.DirectConnection)
        self.trabalhador.finalizado.connect(self.trabalhador.deleteLater)
        self.thread.finished.connect(self._finalizar_thread)
        self.thread.start()

    @pyqtSlot(str, str, object, str)
    def iniciar(self, url: str, perfil: str, bitrate: int | None, destino: str) -> None:
        """Ignora ações repetidas e valida antes de criar trabalho."""
        if self._fechar or self.estado != Estado.PRONTO or self.thread is not None:
            return
        pedido = SolicitacaoDownload(url, perfil, bitrate, Path(destino))
        try:
            pedido.validar()
        except ErroAplicacao as erro:
            self.janela.atualizar_status(str(erro))
            return
        self._tipo_tarefa = "download"
        self._transicionar(Estado.PREPARANDO)
        self.janela.exibir_progresso()
        self._executar_tarefa(
            lambda cancelar, progresso: self.servico.baixar(
                pedido, cancelar, progresso, self.trabalhador.confirmar_substituicao
            )
        )

    @pyqtSlot(str)
    def escolher_pasta(self, inicial: str) -> None:
        """Cancela sem erro; valida e salva a seleção imediatamente."""
        if self._fechar or self.thread is not None:
            return
        escolha = self.janela.escolher_diretorio(inicial)
        if not escolha:
            return
        destino = Path(escolha)
        try:
            self.validar_destino(destino)
            self.salvar_preferencias(destino)
        except (ErroAplicacao, OSError) as erro:
            self.janela.exibir_erro(str(erro))
            return
        self.janela.definir_destino(escolha)
        if self.estado == Estado.PRONTO:
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
    def _ao_substituicao_recusada(self) -> None:
        self._terminal = ("cancelado", "recusado")

    @pyqtSlot(object)
    def _perguntar_substituicao(self, resposta) -> None:
        if self._confirmando_fechamento:
            self._substituicao_pendente = resposta
            return
        try:
            if not self.cancelamento.is_set():
                resposta["aceita"] = self.janela.perguntar_substituicao()
        finally:
            resposta["evento"].set()

    @pyqtSlot()
    def _finalizar_thread(self) -> None:
        self.thread.wait()
        self.thread.deleteLater()
        self.thread = None
        self.trabalhador = None
        self.janela.finalizar_progresso()
        if not self._confirmando_fechamento:
            self._apresentar_resultado()

    def _apresentar_resultado(self) -> None:
        if self._fechar:
            self._concluir_fechamento()
            return
        tipo, valor = self._terminal or ("erro", "O trabalho terminou sem resultado.")
        if self._tipo_tarefa == "ambiente":
            self._finalizar_ambiente(tipo, valor)
            return
        if tipo == "resultado":
            self._transicionar(Estado.CONCLUIDO)
            self.janela.atualizar_status(
                f"{TEXTOS['dl_concluido']}\n{TEXTOS['sucesso'].format(caminho=valor)}"
            )
            self.janela.exibir_sucesso(str(valor))
        elif tipo == "erro":
            self._transicionar(Estado.FALHOU)
            self.janela.atualizar_status(valor)
            self.janela.exibir_erro(valor)
        else:
            self._transicionar(Estado.CANCELADO)
            self.janela.atualizar_status(
                TEXTOS["substituicao_recusada"] if valor == "recusado" else TEXTOS["cancelado"]
            )
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
                self.janela.atualizar_status(erro or TEXTOS["indisponivel"])
                if self.reparo_disponivel is not None:
                    self._oferecer_reparo()
        else:
            self._transicionar(Estado.INDISPONIVEL)
            self.janela.atualizar_status(TEXTOS["indisponivel"])

    def _oferecer_reparo(self) -> None:
        aceito = self.janela.perguntar_reparo()
        if self._fechar:
            return
        if not aceito:
            self.janela.avisar_reparo_manual()
        elif self.reparo_disponivel():
            self.reparo_solicitado = True
            self._concluir_fechamento()
        else:
            self.janela.exibir_erro(TEXTOS["reparo_ausente"])

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
        if self.thread is not None and not self.cancelamento.is_set():
            self.cancelamento.set()
            self._transicionar(Estado.CANCELANDO)
            self.janela.definir_cancelando()

    @pyqtSlot()
    def fechar(self) -> None:
        """Adia fechamento até cleanup sem bloquear a GUI esperando o serviço."""
        if self._confirmando_fechamento:
            return
        if self.thread is None:
            self._concluir_fechamento()
            return
        if self._fechar:
            return
        self._confirmando_fechamento = True
        try:
            aceito = self.estado == Estado.VERIFICANDO or self.janela.perguntar_fechamento()
        finally:
            self._confirmando_fechamento = False
        if aceito:
            self._fechar = True
            self.cancelar()
            self._concluir_fechamento()
        if self._substituicao_pendente is not None:
            resposta = self._substituicao_pendente
            self._substituicao_pendente = None
            self._perguntar_substituicao(resposta)
        if self.thread is None and not aceito:
            self._apresentar_resultado()

    def _concluir_fechamento(self) -> None:
        self._fechar = True
        self.janela.definir_ocupada(True)
        consulta_encerrada = self._atualizacoes is None or self._atualizacoes.encerrar()
        if self.thread is None and consulta_encerrada and self.encerrar_tarefas():
            self.janela.permitir_fechamento()
