"""Fixtures isoladas: nenhuma preferência ou download usa pastas pessoais."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def ferramentas(tmp_path):
    """Caminhos fictícios não dependem de executáveis reais."""
    from dlpdownloader.servicos.dependencias import Ferramentas

    return Ferramentas(*(tmp_path / nome for nome in ("yt.exe", "ff.exe", "probe.exe", "deno.exe")))


@pytest.fixture
def janela(qtbot):
    """Cria view offscreen e evita caixas de mensagem bloqueantes."""
    from dlpdownloader.config.caminhos import caminho_icone
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    view = JanelaPrincipal(caminho_icone())
    view.exibir_erro = lambda mensagem: None
    view.exibir_sucesso = lambda caminho: None
    qtbot.addWidget(view)
    yield view
    view._pode_fechar = True


@pytest.fixture
def pedido(tmp_path):
    """Solicitação válida com diretório temporário já existente."""
    from dlpdownloader.modelos.download import SolicitacaoDownload

    return SolicitacaoDownload("https://example.com/video?a=1&b=2", "mp4", None, Path(tmp_path))
