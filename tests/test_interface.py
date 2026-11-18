"""Ações da janela em uma sessão interativa do Windows."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from config.paths import caminho_icone
from ui.window import JanelaPrincipal

pytestmark = pytest.mark.interface_windows


@pytest.fixture
def janela_isolada(janela_windows):
    janela = JanelaPrincipal(
        caminho_icone(),
        (
            ("mp4", "Vídeo MP4", (), "Melhor vídeo MP4 disponível."),
            ("mp3", "Áudio MP3", (128, 192), "Conversão com bitrate selecionado."),
        ),
    )
    janela.fechamento_solicitado.connect(janela.permitir_fechamento)
    with janela_windows(janela):
        yield janela


def test_escolher_perfil_e_bitrate_emite_download_pelo_botao(janela_isolada, qtbot):
    janela = janela_isolada
    assert not janela.bitrate.isVisible()
    qtbot.mouseClick(janela.url, Qt.MouseButton.LeftButton)
    assert janela.url.hasFocus()
    qtbot.keyClicks(janela.url, "http://127.0.0.1/video.mp4")
    qtbot.mouseClick(janela.formato, Qt.MouseButton.LeftButton)
    QTest.keyClick(janela.formato.view(), Qt.Key.Key_Down)
    QTest.keyClick(janela.formato.view(), Qt.Key.Key_Return)
    assert janela.bitrate.isVisible()
    qtbot.mouseClick(janela.bitrate, Qt.MouseButton.LeftButton)
    QTest.keyClick(janela.bitrate.view(), Qt.Key.Key_Down)
    QTest.keyClick(janela.bitrate.view(), Qt.Key.Key_Return)
    with qtbot.waitSignal(janela.download_solicitado) as sinal:
        qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)
    assert sinal.args == ["http://127.0.0.1/video.mp4", "mp3", 192, ""]


def test_foco_animacao_e_margem_no_redimensionamento(janela_isolada, qtbot):
    janela = janela_isolada
    assert not janela.windowIcon().pixmap(16, 16).isNull()
    qtbot.mouseClick(janela.url, Qt.MouseButton.LeftButton)
    qtbot.keyClick(janela.url, Qt.Key.Key_Tab)
    assert janela.formato.hasFocus()
    qtbot.waitUntil(lambda: janela.formato.realce == 1)
    qtbot.mouseClick(janela.url, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: janela.formato.realce == 0)

    botao = janela.baixar
    geometria = botao.geometry()
    ponto = botao.rect().center()
    ponto.setX(3)
    qtbot.mousePress(botao, Qt.MouseButton.LeftButton, pos=ponto)
    qtbot.waitUntil(lambda: botao.escala < 1)
    assert botao.geometry() == geometria
    with qtbot.waitSignal(janela.download_solicitado):
        qtbot.mouseRelease(botao, Qt.MouseButton.LeftButton, pos=ponto)
    qtbot.waitUntil(lambda: botao.escala == 1)

    espaco = janela.menuBar().cornerWidget(Qt.Corner.TopRightCorner)
    largura_original = espaco.width()
    janela.resize(janela.width() + 200, janela.height())
    qtbot.waitUntil(lambda: espaco.width() == largura_original + 20)
