"""Compõe e inicia a aplicação desktop na arquitetura da raiz."""

import logging
import os
import sys
from contextlib import ExitStack
from functools import partial
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from config.controller import ControladorDownload
from config.paths import caminho_icone, diretorio_dados, raiz_projeto
from config.preferences import Preferencias
from config.version import ler_versao_atual
from services._infra.arquivos import validar_destino
from services._infra.bloqueios import bloquear_uso
from services._infra.dependencias import verificar
from services._models.erros import ErroAplicacao
from services._models.perfis import PERFIS
from services.downloader import ServicoDownload
from services.repair import iniciar_reparo, reparo_disponivel
from services.updater import verificar_atualizacao
from ui.tema import aplicar_tema
from ui.text import TEXTOS, TITULO
from ui.window import JanelaPrincipal


def _consultar_atualizacao(cancelamento):
    return verificar_atualizacao(ler_versao_atual(), cancelamento)


def criar_aplicacao(
    app: QApplication,
    *,
    raiz: Path | None = None,
    dados: Path | None = None,
    destino_padrao: Path | None = None,
) -> tuple[JanelaPrincipal, ControladorDownload]:
    """Monta a janela e o controlador antes de iniciar as tarefas e o loop."""
    raiz = raiz_projeto() if raiz is None else raiz.resolve()
    dados = diretorio_dados() if dados is None else dados
    if destino_padrao is None:
        destino_padrao = Path(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        )
    icone = caminho_icone()
    app.setApplicationName("DLPDownloader")
    app.setWindowIcon(QIcon(str(icone)))
    aplicar_tema(app)
    perfis = tuple(
        (identificador, rotulo, bitrates, ajuda)
        for identificador, rotulo, _, bitrates, ajuda in PERFIS
    )
    janela = JanelaPrincipal(icone, perfis)
    preferencias = Preferencias(dados / "config.json", destino_padrao)
    controlador = ControladorDownload(
        janela,
        carregar_preferencias=preferencias.carregar,
        salvar_preferencias=preferencias.salvar,
        validar_destino=validar_destino,
        verificar=partial(verificar, raiz),
        criar_servico=ServicoDownload,
        reparo_disponivel=partial(reparo_disponivel, raiz),
        consultar_atualizacao=None if os.environ.get("DLP_SMOKE_TEST") else _consultar_atualizacao,
        abrir_release=lambda url: QDesktopServices.openUrl(QUrl(url)),
    )
    return janela, controlador


def configurar_logs(dados: Path) -> None:
    """Grava registros com rotação e recorre ao console se a pasta falhar."""
    try:
        dados.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            dados / "aplicacao.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        logging.basicConfig(level=logging.INFO, handlers=[handler])
    except OSError:
        logging.basicConfig(level=logging.INFO)


def main() -> int:
    """Inicia o Qt e verifica as ferramentas depois de mostrar a janela."""
    app = QApplication(sys.argv)
    raiz, dados = raiz_projeto(), diretorio_dados()
    with ExitStack() as recursos:
        try:
            recursos.enter_context(bloquear_uso(dados, exclusivo=False))
        except (OSError, RuntimeError):
            QMessageBox.warning(None, TITULO, TEXTOS["aguardar_reparo"])
            return 1
        configurar_logs(dados)
        try:
            logging.info("Versão da aplicação: %s", ler_versao_atual() or "desenvolvimento")
        except ErroAplicacao:
            logging.warning(
                "Versão da distribuição indisponível; downloads permanecem disponíveis."
            )
        janela, controlador = criar_aplicacao(app, raiz=raiz, dados=dados)
        janela.show()
        QTimer.singleShot(0, controlador.inicializar)
        resultado = app.exec()
    if controlador.reparo_solicitado:
        try:
            iniciar_reparo(raiz)
        except OSError:
            QMessageBox.critical(None, TITULO, TEXTOS["erro_iniciar_reparo"])
            return 1
    return resultado


if __name__ == "__main__":
    raise SystemExit(main())
