"""Aplicação real no desktop Windows, com serviços e mídia locais."""

import functools
import http.server
import json
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox

from config.bootstrap import criar_aplicacao
from services._infra.dependencias import localizar

pytestmark = pytest.mark.interface_windows
RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def midia_gui(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("midia-interface")
    ferramentas = localizar(RAIZ)
    subprocess.run(
        [
            str(ferramentas.ffmpeg),
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=160x90:rate=10",
            "-f",
            "lavfi",
            "-i",
            "sine=sample_rate=48000",
            "-t",
            "1",
            "-c:v",
            "mpeg4",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(pasta / "fonte.mp4"),
        ],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(pasta))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as servidor:
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{servidor.server_port}/fonte.mp4"
        finally:
            servidor.shutdown()
            thread.join(timeout=5)


@pytest.fixture
def aplicacao(qapp, qtbot, janela_windows, tmp_path):
    dados = tmp_path / "dados"
    destino = tmp_path / "downloads"
    destino.mkdir()
    janela, controlador = criar_aplicacao(qapp, raiz=RAIZ, dados=dados, destino_padrao=destino)
    with janela_windows(janela):
        controlador.inicializar()
        qtbot.waitUntil(janela.baixar.isEnabled, timeout=15000)
        yield janela, destino, dados


@contextmanager
def responder_caixa(qtbot, texto, *, papel=None):
    """Aciona o botão quando a caixa real entra no loop modal."""
    respondida = []
    timer = QTimer()

    def responder():
        caixa = QApplication.activeModalWidget()
        if not isinstance(caixa, QMessageBox) or texto not in caixa.text():
            return
        botao = next(b for b in caixa.buttons() if papel is None or caixa.buttonRole(b) == papel)
        respondida.append(caixa.text())
        timer.stop()
        qtbot.mouseClick(botao, Qt.MouseButton.LeftButton)

    timer.timeout.connect(responder)
    timer.start(20)
    try:
        yield
        qtbot.waitUntil(lambda: bool(respondida), timeout=15000)
    finally:
        timer.stop()


def solicitar_download(qtbot, janela, url):
    qtbot.mouseClick(janela.url, Qt.MouseButton.LeftButton)
    qtbot.keyClick(janela.url, Qt.Key.Key_A, modifier=Qt.KeyboardModifier.ControlModifier)
    qtbot.keyClicks(janela.url, url)
    qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)


def test_baixa_video_pela_janela_e_recusa_substituir(aplicacao, midia_gui, qtbot):
    janela, destino, _ = aplicacao
    with responder_caixa(qtbot, "Download concluído"):
        solicitar_download(qtbot, janela, midia_gui)
    qtbot.waitUntil(janela.baixar.isEnabled)
    resultado = destino / "fonte [fonte].mp4"
    assert resultado.stat().st_size > 0
    resultado.write_bytes(b"arquivo existente")

    with responder_caixa(qtbot, "O arquivo já existe", papel=QMessageBox.ButtonRole.NoRole):
        solicitar_download(qtbot, janela, midia_gui)
    qtbot.waitUntil(janela.baixar.isEnabled)
    assert resultado.read_bytes() == b"arquivo existente"
    assert list(destino.iterdir()) == [resultado]
    assert janela.status.text() == "O arquivo existente foi mantido."


def test_baixa_audio_no_destino_restaurado(midia_gui, janela_windows, qapp, qtbot, tmp_path):
    dados = tmp_path / "dados"
    destino_padrao = tmp_path / "outro"
    destino = tmp_path / "audio"
    destino.mkdir()
    dados.mkdir()
    (dados / "config.json").write_text(
        json.dumps({"versao": 1, "diretorio": str(destino)}), encoding="utf-8"
    )
    janela, controlador = criar_aplicacao(
        qapp, raiz=RAIZ, dados=dados, destino_padrao=destino_padrao
    )
    with janela_windows(janela):
        controlador.inicializar()
        qtbot.waitUntil(janela.baixar.isEnabled, timeout=15000)
        assert Path(janela.destino.text()) == destino
        qtbot.mouseClick(janela.formato, Qt.MouseButton.LeftButton)
        for _ in range(3):
            QTest.keyClick(janela.formato.view(), Qt.Key.Key_Down)
        QTest.keyClick(janela.formato.view(), Qt.Key.Key_Return)
        qtbot.mouseClick(janela.bitrate, Qt.MouseButton.LeftButton)
        QTest.keyClick(janela.bitrate.view(), Qt.Key.Key_Down)
        QTest.keyClick(janela.bitrate.view(), Qt.Key.Key_Return)
        with responder_caixa(qtbot, "Download concluído"):
            solicitar_download(qtbot, janela, midia_gui)
    resultado = destino / "fonte [fonte] - 192k.mp3"
    ffprobe = localizar(RAIZ).ffprobe
    sondagem = json.loads(
        subprocess.check_output(
            [str(ffprobe), "-v", "error", "-show_streams", "-of", "json", str(resultado)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    )
    assert [(f["codec_name"], f["bit_rate"]) for f in sondagem["streams"]] == [("mp3", "192000")]
    assert list(destino.iterdir()) == [resultado]
