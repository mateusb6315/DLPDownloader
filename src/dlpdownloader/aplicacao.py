"""Raiz de composição: instancia dependências, configura logs e inicia a GUI."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from PyQt6.QtCore import QStandardPaths, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from dlpdownloader.config.caminhos import caminho_icone, diretorio_dados, raiz_projeto
from dlpdownloader.config.versao import build_beta, versao_atual
from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
from dlpdownloader.controladores.download import ControladorDownload
from dlpdownloader.modelos.erros import ErroAplicacao
from dlpdownloader.servicos.dependencias import verificar
from dlpdownloader.servicos.preferencias import Preferencias
from dlpdownloader.servicos.updates import update_service
from dlpdownloader.servicos.yt_dlp import ServicoDownload
from dlpdownloader.visoes.janela_principal import JanelaPrincipal
from dlpdownloader.visoes.tema import aplicar_tema


def main() -> int:
    """Inicia aplicação com recursos independentes do diretório de trabalho."""
    from pathlib import Path

    if len(sys.argv) == 3 and sys.argv[1] == "--verificar-midia":
        from dlpdownloader.servicos.arquivos import gravar_json
        from dlpdownloader.servicos.autoteste import testar_midia

        dados_teste = Path(sys.argv[2])
        try:
            testar_midia(raiz_projeto(), dados_teste)
        except Exception as erro:
            # Uma falha na CI não deve abrir o diálogo de traceback do PyInstaller.
            try:
                gravar_json(
                    dados_teste / "resultado.json", {"sucesso": False, "erro": type(erro).__name__}
                )
            except OSError:
                pass
            return 1
        return 0

    app = QApplication(sys.argv)
    from dlpdownloader.servicos.uso import bloquear_uso

    trava = bloquear_uso(diretorio_dados(), exclusivo=False)
    try:
        trava.__enter__()
    except (OSError, RuntimeError):
        QMessageBox.warning(
            None, "DLP Downloader", "Aguarde o reparo terminar antes de abrir o aplicativo."
        )
        return 1
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
    reparo_solicitado = False

    def solicitar_reparo() -> bool:
        nonlocal reparo_solicitado
        if not (raiz_projeto() / "vendor/repair.exe").is_file():
            return False
        reparo_solicitado = True
        return True

    controlador = ControladorDownload(
        janela,
        preferencias,
        lambda cancelar: verificar(raiz_projeto(), cancelar),
        ServicoDownload,
        solicitar_reparo,
    )
    atualizacoes = ControladorAtualizacoes(
        janela,
        update_service,
        versao_atual,
        lambda url: QDesktopServices.openUrl(QUrl(url)),
        build_beta,
    )
    janela.antes_de_fechar = atualizacoes.encerrar
    try:
        logging.info(
            "Versão da aplicação: %s%s",
            versao_atual() or "desenvolvimento",
            " (beta)" if build_beta() else "",
        )
    except ErroAplicacao:
        logging.warning("Versão da distribuição indisponível; downloads permanecem disponíveis.")
    janela.show()
    if not os.environ.get("DLP_SMOKE_TEST"):
        QTimer.singleShot(0, atualizacoes.iniciar)
    QTimer.singleShot(0, controlador.inicializar)
    try:
        resultado = app.exec()
    finally:
        trava.__exit__(None, None, None)
    if reparo_solicitado:
        from dlpdownloader.servicos.reparo import iniciar_reparo

        try:
            iniciar_reparo(raiz_projeto())
        except OSError:
            QMessageBox.critical(
                None, "DLP Downloader", "Não foi possível iniciar vendor/repair.exe."
            )
            return 1
    return resultado
