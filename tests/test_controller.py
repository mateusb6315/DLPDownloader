"""Falha e limpeza controladas no mediador da arquitetura raiz."""

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import Qt

from config.controller import ControladorDownload
from config.paths import caminho_icone
from config.preferences import Preferencias
from services._infra.arquivos import validar_destino
from services._models.download import Estado
from services._models.erros import Cancelado, ErroDownload
from services._models.progresso import EventoProgresso
from ui.window import JanelaPrincipal


@pytest.fixture
def preparar(qtbot, tmp_path):
    def montar(baixar):
        janela = JanelaPrincipal(caminho_icone(), (("mp4", "Vídeo MP4", (), ""),))
        qtbot.addWidget(janela)
        preferencias = Preferencias(tmp_path / "dados/config.json", tmp_path)
        controlador = ControladorDownload(
            janela,
            carregar_preferencias=preferencias.carregar,
            salvar_preferencias=preferencias.salvar,
            validar_destino=validar_destino,
            verificar=lambda cancelar: object(),
            criar_servico=lambda ferramentas: SimpleNamespace(baixar=baixar),
        )
        janela.show()
        controlador.inicializar()
        qtbot.waitUntil(janela.baixar.isEnabled)
        qtbot.keyClicks(janela.url, "https://example.com/video")
        return janela, controlador

    return montar


def test_escolha_da_pasta_persiste_e_considera_destino_anterior(preparar, qtbot, tmp_path):
    janela, _ = preparar(None)
    destino = tmp_path / "escolhido"
    destino.mkdir()
    iniciais = []

    def escolher(inicial):
        iniciais.append(Path(inicial))
        return str(destino) if len(iniciais) == 1 else ""

    janela.escolher_diretorio = escolher
    qtbot.mouseClick(janela.escolher, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(janela.escolher, Qt.MouseButton.LeftButton)
    assert iniciais == [tmp_path, destino]
    assert Preferencias(tmp_path / "dados/config.json", tmp_path).carregar() == (destino, "")
    assert Path(janela.destino.text()) == destino


def test_erro_apos_progresso_fecha_popup_e_retorna_ao_pronto(preparar, qtbot):
    def baixar(_pedido, _cancelar, progresso, _confirmar):
        progresso(EventoProgresso("baixando", "vídeo", 50, 100))
        progresso(EventoProgresso("finalizando"))
        raise ErroDownload("Falha na junção.")

    janela, controlador = preparar(baixar)
    erros, sucessos = [], []
    janela.exibir_erro = erros.append
    janela.exibir_sucesso = sucessos.append
    qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: controlador.estado == Estado.PRONTO)
    assert controlador.thread is None
    assert janela.popup is None and janela.baixar.isEnabled()
    assert erros == ["Falha na junção."] and not sucessos


def test_fechar_durante_download_aguarda_cleanup_do_trabalhador(preparar, qtbot):
    iniciou = threading.Event()
    cancelou = threading.Event()
    liberar = threading.Event()

    def baixar(pedido, cancelar, _progresso, _confirmar):
        temporario = Path(pedido.destino) / "parcial"
        temporario.touch()
        iniciou.set()
        try:
            assert cancelar.wait(5)
            cancelou.set()
            assert liberar.wait(5)
            raise Cancelado()
        finally:
            temporario.unlink()

    janela, controlador = preparar(baixar)
    janela.perguntar_fechamento = lambda: True
    qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)
    try:
        qtbot.waitUntil(iniciou.is_set)
        janela.close()
        qtbot.waitUntil(cancelou.is_set)
        assert janela.isVisible() and janela.popup is not None
        assert controlador.estado == Estado.CANCELANDO
    finally:
        liberar.set()
        qtbot.waitUntil(lambda: controlador.thread is None)
    qtbot.waitUntil(lambda: not janela.isVisible())
    assert janela.popup is None
    assert not list(Path(janela.destino.text()).iterdir())
