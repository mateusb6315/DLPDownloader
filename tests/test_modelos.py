"""Validação e seleção de saída sem rede ou filesystem pessoal."""

from dataclasses import replace

import pytest

from dlpdownloader.modelos.erros import ErroAplicacao
from dlpdownloader.modelos.formatos import argumentos_formato


@pytest.mark.parametrize(
    "url",
    [
        "",
        "texto",
        "file:///x",
        "ftp://host/a",
        "https://",
        "https://a/a b",
        "https://user:senha@host/a",
        "https://[",
        "https://host:invalido/a",
    ],
)
def test_url_invalida_nao_inicia(pedido, url):
    with pytest.raises(ErroAplicacao):
        replace(pedido, url=url).validar()


@pytest.mark.parametrize(
    "url",
    [
        "https://youtu.be/abc",
        "http://localhost:8000/v.mp4",
        "https://www.youtube.com/watch?v=abc&list=xyz",
    ],
)
def test_url_http_valida(pedido, url):
    replace(pedido, url=url).validar()


@pytest.mark.parametrize(
    "perfil,bitrate",
    [("mp4", 128), ("flac", 320), ("mp3", None), ("m4a", 320), ("inexistente", None)],
)
def test_opcoes_invalidas_rejeitadas(pedido, perfil, bitrate):
    with pytest.raises(ErroAplicacao):
        replace(pedido, perfil=perfil, bitrate=bitrate).validar()


def test_seletores_sao_dinamicos_sem_ids_fixos(pedido):
    argumentos = argumentos_formato(pedido)
    assert argumentos[argumentos.index("-f") + 1] == "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
    mkv = argumentos_formato(replace(pedido, perfil="mkv"))
    assert "bv+ba/b" in mkv
    assert "299" not in str(argumentos) and "140" not in str(argumentos)


def test_bitrate_nao_e_permitido_para_lossless(pedido):
    replace(pedido, perfil="flac").validar()
    assert argumentos_formato(replace(pedido, perfil="flac"))[-1] == "flac"


def test_estado_nao_permite_download_antes_de_pronto():
    from dlpdownloader.modelos.download import Estado, validar_transicao

    with pytest.raises(ValueError, match="Transição inválida"):
        validar_transicao(Estado.VERIFICANDO, Estado.BAIXANDO)
    validar_transicao(Estado.PRONTO, Estado.PREPARANDO)
