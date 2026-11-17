"""Consultas de releases por operações injetadas no mediador."""

import json
import sys
import threading
from io import BytesIO
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import Qt

from config.controller import ControladorDownload
from config.paths import caminho_icone
from services._models.atualizacoes import ReleaseEstavel, ResultadoConsulta, VersaoDistribuicao
from services._models.erros import Cancelado, ErroAplicacao
from services.updater import verificar_atualizacao
from ui.window import JanelaPrincipal

URL_RELEASE = "https://github.com/mateusb6315/DLPDownloader/releases/tag/v1.10.0"


def test_versao_incorporada_prevalece_em_instalacao_atualizada(monkeypatch, tmp_path):
    from config import version

    (tmp_path / "version.json").write_text('{"version":"1.2.1"}', encoding="utf-8")
    monkeypatch.setattr(version, "em_distribuicao", lambda: True)
    monkeypatch.setattr(version, "raiz_projeto", lambda: tmp_path)
    monkeypatch.setitem(sys.modules, "versao_build", SimpleNamespace(VERSAO="1.3.1", BETA=True))
    assert version.ler_versao_atual() == VersaoDistribuicao("1.3.1", True)


@pytest.mark.parametrize(
    "local,beta,oferece",
    [
        ("1.9.0", False, True),
        ("1.10.0", True, True),
        ("1.10.0", False, False),
        ("1.11.0", True, False),
    ],
)
def test_compara_versoes_estaveis_e_oferece_release_da_beta(local, beta, oferece):
    def abrir(_pedido, *, timeout):
        assert timeout > 0
        resposta = BytesIO(
            json.dumps(
                {
                    "tag_name": "v1.10.0",
                    "html_url": URL_RELEASE,
                    "draft": False,
                    "prerelease": False,
                }
            ).encode()
        )
        resposta.status = 200
        return resposta

    resultado = verificar_atualizacao(
        VersaoDistribuicao(local, beta), threading.Event(), abrir=abrir
    )

    assert resultado.versao_atual == (local + " (beta)" if beta else local)
    if oferece:
        assert resultado.disponivel.versao == "1.10.0"
        assert resultado.disponivel.url == URL_RELEASE
    else:
        assert resultado.disponivel is None


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"draft": True},
        {"prerelease": True},
        {"tag_name": "v1.10.0-beta"},
        {"html_url": "https://example.com/release"},
        {"html_url": "https://github.com/mateusb6315/DLPDownloader/releases/tag/v2.0.0"},
    ],
)
def test_resposta_invalida_nao_equivale_a_aplicativo_atualizado(alteracoes):
    def abrir(_pedido, *, timeout):
        release = {
            "tag_name": "v1.10.0",
            "html_url": URL_RELEASE,
            "draft": False,
            "prerelease": False,
        }
        resposta = BytesIO(json.dumps(release | alteracoes).encode())
        resposta.status = 200
        return resposta

    with pytest.raises(ErroAplicacao, match="Não foi possível verificar"):
        verificar_atualizacao(VersaoDistribuicao("1.3.1"), threading.Event(), abrir=abrir)


def test_execucao_por_fonte_nao_consulta_a_rede():
    from config.version import ler_versao_atual

    def abrir(*_args, **_kwargs):
        pytest.fail("A execução por fonte não deve consultar o GitHub.")

    with pytest.raises(ErroAplicacao, match="Use uma distribuição compilada"):
        verificar_atualizacao(ler_versao_atual(), threading.Event(), abrir=abrir)


@pytest.fixture
def montar(qtbot, tmp_path):
    def iniciar(consultar, abrir_release, baixar=None):
        janela = JanelaPrincipal(caminho_icone(), (("mp4", "Vídeo MP4", (), ""),))
        qtbot.addWidget(janela)
        controlador = ControladorDownload(
            janela,
            carregar_preferencias=lambda: (tmp_path, ""),
            salvar_preferencias=lambda _destino: None,
            validar_destino=lambda _destino: None,
            verificar=lambda _cancelar: object(),
            criar_servico=lambda _ferramentas: SimpleNamespace(baixar=baixar),
            consultar_atualizacao=consultar,
            abrir_release=abrir_release,
        )
        janela.show()
        controlador.inicializar()
        qtbot.waitUntil(janela.baixar.isEnabled)
        return janela

    return iniciar


def test_consulta_manual_durante_download(montar, qtbot):
    consultas = []
    iniciou_download = threading.Event()
    terminou_download = threading.Event()

    def consultar(_cancelar):
        consultas.append(threading.get_ident())
        return ResultadoConsulta("1.3.1", None)

    def baixar(_pedido, cancelar, _progresso, _confirmar):
        iniciou_download.set()
        try:
            assert cancelar.wait(5)
            raise Cancelado()
        finally:
            terminou_download.set()

    janela = montar(consultar, lambda _url: True, baixar)
    qtbot.waitUntil(lambda: consultas and janela.acao_atualizar.isEnabled())
    mensagens = []
    janela.informar_atualizado = mensagens.append
    qtbot.keyClicks(janela.url, "https://example.com/video")
    qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(iniciou_download.is_set)
    try:
        assert janela.acao_atualizar.isEnabled()
        assert not janela.popup.isModal()
        janela.acao_atualizar.trigger()
        qtbot.waitUntil(lambda: mensagens == ["1.3.1"])
        assert not janela.baixar.isEnabled() and not terminou_download.is_set()
        assert len(consultas) == 2
        assert threading.get_ident() not in consultas
    finally:
        qtbot.mouseClick(janela.popup.cancelar, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(janela.baixar.isEnabled)


def test_consulta_automatica_oferece_release_e_abre_navegador(montar, qtbot):
    pode_retornar = threading.Event()

    def consultar(_cancelamento):
        assert pode_retornar.wait(5)
        return ResultadoConsulta("1.10.0 (beta)", ReleaseEstavel("1.10.0", URL_RELEASE))

    ofertas, links = [], []
    janela = montar(consultar, lambda url: links.append(url) or True)
    janela.oferecer_atualizacao = lambda local, remota: ofertas.append((local, remota)) or True
    pode_retornar.set()
    qtbot.waitUntil(lambda: links == [URL_RELEASE])
    assert ofertas == [("1.10.0 (beta)", "1.10.0")]
    assert janela.consulta is None


def test_cancelar_consulta_manual_descarta_resultado_e_reabilita_menu(montar, qtbot):
    cancelado = threading.Event()
    liberar = threading.Event()
    resultados = []

    def consultar(cancelamento):
        if resultados:
            assert cancelamento.wait(5)
            cancelado.set()
            assert liberar.wait(5)
        resultados.append("1.3.1")
        return ResultadoConsulta("1.3.1", None)

    janela = montar(consultar, lambda _url: True)
    qtbot.waitUntil(janela.acao_atualizar.isEnabled)
    avisos = []
    janela.informar_atualizado = avisos.append
    janela.acao_atualizar.trigger()
    try:
        qtbot.mouseClick(janela.consulta.cancelar, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(cancelado.is_set)
        assert janela.baixar.isEnabled() and not janela.acao_atualizar.isEnabled()
    finally:
        liberar.set()
    qtbot.waitUntil(janela.acao_atualizar.isEnabled)
    assert janela.consulta is None and avisos == []


def test_fechar_aguarda_download_e_consulta_cancelados(montar, qtbot):
    consulta_cancelada = threading.Event()
    download_iniciado = threading.Event()
    download_cancelado = threading.Event()
    liberar_consulta, liberar_download = threading.Event(), threading.Event()

    def consultar(cancelamento):
        assert cancelamento.wait(5)
        consulta_cancelada.set()
        assert liberar_consulta.wait(5)
        return ResultadoConsulta("1.3.1", ReleaseEstavel("1.10.0", URL_RELEASE))

    def baixar(_pedido, cancelamento, _progresso, _confirmar):
        download_iniciado.set()
        assert cancelamento.wait(5)
        download_cancelado.set()
        assert liberar_download.wait(5)
        raise Cancelado()

    janela = montar(consultar, lambda _url: pytest.fail("O aplicativo está fechando."), baixar)
    janela.perguntar_fechamento = lambda: True
    qtbot.keyClicks(janela.url, "https://example.com/video")
    qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)
    try:
        qtbot.waitUntil(download_iniciado.is_set)
        janela.close()
        qtbot.waitUntil(consulta_cancelada.is_set)
        qtbot.waitUntil(download_cancelado.is_set)
        assert janela.isVisible() and janela.popup is not None
        liberar_download.set()
        qtbot.waitUntil(lambda: janela.popup is None)
        assert janela.isVisible()
    finally:
        liberar_download.set()
        liberar_consulta.set()
        qtbot.waitUntil(lambda: not janela.isVisible())


@pytest.mark.parametrize(
    "conteudo",
    [None, "{", "[]", "{}", '{"version":3}', '{"version":"beta"}', "x" * 5000, '{"version":"1.2"}'],
)
def test_distribuicao_sem_versao_incorporada_rejeita_metadados_invalidos(
    tmp_path, monkeypatch, conteudo
):
    from config import version

    if conteudo is not None:
        (tmp_path / "version.json").write_text(conteudo, encoding="utf-8")
    monkeypatch.setattr(version, "em_distribuicao", lambda: True)
    monkeypatch.setattr(version, "raiz_projeto", lambda: tmp_path)
    monkeypatch.delitem(sys.modules, "versao_build", raising=False)

    with pytest.raises(ErroAplicacao, match="Não foi possível verificar a versão atual"):
        version.ler_versao_atual()


def test_distribuicao_sem_versao_incorporada_reconhece_metadados_anteriores(tmp_path, monkeypatch):
    from config import version

    (tmp_path / "version.json").write_text('{"version":"1.2.1"}', encoding="utf-8")
    monkeypatch.setattr(version, "em_distribuicao", lambda: True)
    monkeypatch.setattr(version, "raiz_projeto", lambda: tmp_path)
    monkeypatch.delitem(sys.modules, "versao_build", raising=False)

    assert version.ler_versao_atual() == VersaoDistribuicao("1.2.1")
