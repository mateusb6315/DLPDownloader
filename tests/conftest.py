"""Fixtures isoladas: nenhuma preferência ou download usa pastas pessoais."""

import os
from contextlib import contextmanager
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def janela_windows(qapp, qtbot):
    """Exige uma janela ativa no desktop, com eventos reais do Qt."""
    from PyQt6.QtTest import QTest

    assert qapp.platformName() == "windows", "Execute com QT_QPA_PLATFORM=windows."

    @contextmanager
    def mostrar(janela):
        janela.show()
        janela.raise_()
        janela.activateWindow()
        try:
            assert QTest.qWaitForWindowActive(janela, 5000), "Desktop Windows indisponível."
            yield janela
        finally:
            janela.close()
            qtbot.waitUntil(lambda: not janela.isVisible(), timeout=10000)

    return mostrar


@pytest.fixture
def ferramentas(tmp_path):
    """Caminhos fictícios não dependem de executáveis reais."""
    from services._infra.dependencias import Ferramentas

    return Ferramentas(*(tmp_path / nome for nome in ("yt.exe", "ff.exe", "probe.exe", "deno.exe")))


@pytest.fixture
def pedido(tmp_path):
    """Solicitação válida com diretório temporário já existente."""
    from services._models.download import SolicitacaoDownload

    return SolicitacaoDownload("https://example.com/video?a=1&b=2", "mp4", None, Path(tmp_path))
