"""Regras de atualização e protocolo remoto sem acesso real à rede."""

import json
from unittest.mock import MagicMock

import pytest

from dlpdownloader.modelos.atualizacoes import normalizar_versao
from dlpdownloader.modelos.erros import ErroAplicacao
from dlpdownloader.servicos.updates import update_service


def test_comparacao_numerica():
    assert normalizar_versao("v1.10.0") > normalizar_versao("1.9.0")
    with pytest.raises(ErroAplicacao):
        normalizar_versao("1.2.0-beta")


@pytest.mark.parametrize(
    "url,esperado",
    [
        ("https://github.com/mateusb6315/DLPDownloader/releases/tag/v1.3.0", True),
        ("https://example.com/release", False),
    ],
)
def test_servico_valida_release(monkeypatch, url, esperado):
    resposta = MagicMock()
    resposta.status = 200
    resposta.read.return_value = json.dumps(
        {"tag_name": "v1.3.0", "html_url": url, "draft": False, "prerelease": False}
    ).encode()
    contexto = MagicMock()
    contexto.__enter__.return_value = resposta
    monkeypatch.setattr("dlpdownloader.servicos.updates.urlopen", lambda *a, **k: contexto)
    if esperado:
        assert update_service() == ((1, 3, 0), url)
    else:
        with pytest.raises(ErroAplicacao):
            update_service()


@pytest.mark.parametrize(
    "manual,nova,avisos", [(False, False, 0), (False, True, 1), (True, False, 0)]
)
def test_fluxos_qt(qtbot, manual, nova, avisos):
    from pathlib import Path

    from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(Path("flet.png"))
    qtbot.addWidget(janela)
    janela.oferecer_atualizacao = MagicMock(return_value=True)
    janela.informar_atualizado = MagicMock()
    abrir = MagicMock(return_value=True)
    controlador = ControladorAtualizacoes(
        janela,
        lambda: ((1, 3, 0) if nova else (1, 2, 0), "https://github.com/release"),
        lambda: "1.2.0",
        abrir,
    )
    controlador.iniciar(manual)
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert janela.oferecer_atualizacao.call_count == avisos
    assert abrir.call_count == avisos
    assert janela.informar_atualizado.call_count == int(manual and not nova)
    assert janela.consulta is None
    controlador.encerrar()


@pytest.mark.parametrize(
    "conteudo",
    [None, "{", "[]", "{}", '{"version":3}', '{"version":"beta"}', "x" * 5000, '{"version":"1.2"}'],
)
def test_json_invalido_nao_tem_fallback(tmp_path, conteudo):
    from dlpdownloader.config.versao import ERRO_VERSAO, ler_versao

    caminho = tmp_path / "version.json"
    if conteudo is not None:
        caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroAplicacao) as erro:
        ler_versao(caminho)
    assert str(erro.value) == ERRO_VERSAO


def test_versao_compilada_independe_do_diretorio_e_metadata(tmp_path, monkeypatch):
    from dlpdownloader.config import versao

    (tmp_path / "version.json").write_text('{"version":"1.2.1"}')
    monkeypatch.setattr(versao.sys, "executable", str(tmp_path / "DLPDownloader.exe"))
    monkeypatch.setattr(versao.sys, "frozen", True, raising=False)
    assert versao.versao_atual() == "1.2.1"
    monkeypatch.setattr(versao.sys, "frozen", False)
    assert versao.versao_atual() is None


@pytest.mark.parametrize("manual", [True, False])
@pytest.mark.parametrize("local", ["1.2.1", "1.10.0"])
def test_igual_ou_superior_nao_oferece_downgrade(qtbot, manual, local):
    from pathlib import Path

    from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(Path("flet.png"))
    qtbot.addWidget(janela)
    janela.oferecer_atualizacao = MagicMock()
    janela.informar_atualizado = MagicMock()
    controle = ControladorAtualizacoes(
        janela, lambda: ((1, 2, 1), "url"), lambda: local, MagicMock()
    )
    controle.iniciar(manual)
    qtbot.waitUntil(lambda: controle.thread is None)
    janela.oferecer_atualizacao.assert_not_called()
    if manual:
        janela.informar_atualizado.assert_called_once_with(local)
    else:
        janela.informar_atualizado.assert_not_called()
    controle.encerrar()


@pytest.mark.parametrize("manual", [True, False])
def test_erro_de_versao_restaura_interface(qtbot, manual):
    from pathlib import Path

    from dlpdownloader.config.versao import ERRO_VERSAO
    from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(Path("flet.png"))
    qtbot.addWidget(janela)
    janela.exibir_erro = MagicMock()
    consultar = MagicMock()

    def falhar():
        raise ErroAplicacao(ERRO_VERSAO)

    controle = ControladorAtualizacoes(janela, consultar, falhar, MagicMock())
    controle.iniciar(manual)
    qtbot.waitUntil(lambda: controle.thread is None)
    consultar.assert_not_called()
    assert janela.consulta is None
    assert janela.acao_atualizar.isEnabled()
    assert janela.baixar.isEnabled()
    assert janela.exibir_erro.call_count == int(manual)
    controle.encerrar()


def test_desenvolvimento_nao_consulta_github(qtbot):
    from pathlib import Path

    from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(Path("flet.png"))
    qtbot.addWidget(janela)
    consultar = MagicMock()
    controle = ControladorAtualizacoes(janela, consultar, lambda: None, MagicMock())
    controle.iniciar()
    qtbot.waitUntil(lambda: controle.thread is None)
    consultar.assert_not_called()
    controle.encerrar()


def test_beta_oferece_estavel_de_mesma_versao(qtbot):
    from pathlib import Path

    from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(Path("flet.png"))
    qtbot.addWidget(janela)
    janela.oferecer_atualizacao = MagicMock(return_value=False)
    controle = ControladorAtualizacoes(
        janela,
        lambda: ((1, 3, 0), "https://github.com/release"),
        lambda: "1.3.0",
        MagicMock(),
        lambda: True,
    )
    controle.iniciar(True)
    qtbot.waitUntil(lambda: controle.thread is None)
    janela.oferecer_atualizacao.assert_called_once_with("1.3.0 (beta)", "1.3.0")
    controle.encerrar()


def test_versao_incorporada_prioritaria_no_pacote(monkeypatch):
    import sys
    from types import SimpleNamespace

    from dlpdownloader.config import versao

    monkeypatch.setattr(versao.sys, "frozen", True, raising=False)
    monkeypatch.setitem(sys.modules, "versao_build", SimpleNamespace(VERSAO="1.3.0", BETA=True))
    assert versao.versao_atual() == "1.3.0" and versao.build_beta()


@pytest.mark.parametrize("nome,esperado", [("1.3.0_beta3", "1.3.0"), ("ensaio", "1.4.0")])
def test_beta_incorpora_versao_sem_metadados_externos(tmp_path, nome, esperado):
    from scripts.versao_build import preparar_versao

    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.4.0"')
    preparar_versao(tmp_path, tmp_path, nome, beta=True)
    dados = {}
    exec((tmp_path / "versao_build.py").read_text(), dados)
    assert dados["VERSAO"] == esperado and dados["BETA"] is True


def test_menu_opcoes_dispara_consulta(qtbot):
    from pathlib import Path

    from PyQt6.QtCore import Qt

    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(Path("flet.png"))
    qtbot.addWidget(janela)
    sinal = MagicMock()
    janela.atualizacao_solicitada.connect(sinal)
    assert janela.menuBar().cornerWidget(Qt.Corner.TopRightCorner) is not None
    janela.acao_atualizar.trigger()
    sinal.assert_called_once()


def test_aceitar_reparo_aguarda_consulta_antes_de_fechar(qtbot, tmp_path):
    import threading

    from dlpdownloader.controladores.atualizacoes import ControladorAtualizacoes
    from dlpdownloader.controladores.download import ControladorDownload
    from dlpdownloader.modelos.erros import ErroDependencia
    from dlpdownloader.servicos.preferencias import Preferencias
    from dlpdownloader.visoes.janela_principal import JanelaPrincipal

    janela = JanelaPrincipal(tmp_path / "icone.png")
    qtbot.addWidget(janela)
    janela.show()
    janela.perguntar_reparo = lambda: True
    liberacao, iniciou = threading.Event(), threading.Event()

    def consultar():
        iniciou.set()
        liberacao.wait(5)
        return (1, 3, 0), "https://github.com/release"

    atualizacoes = ControladorAtualizacoes(janela, consultar, lambda: "1.3.0", MagicMock())
    janela.antes_de_fechar = atualizacoes.encerrar
    atualizacoes.iniciar()
    qtbot.waitUntil(iniciou.is_set)
    solicitou = []

    def ausente(evento):
        raise ErroDependencia("ausente")

    download = ControladorDownload(
        janela,
        Preferencias(tmp_path / "prefs.json", tmp_path),
        ausente,
        lambda ferramentas: None,
        lambda: solicitou.append(True) or True,
    )
    try:
        download.inicializar()
        qtbot.waitUntil(lambda: download.thread is None)
        assert solicitou == [True] and janela.isVisible()
    finally:
        liberacao.set()
    qtbot.waitUntil(lambda: atualizacoes.thread is None and not janela.isVisible())
