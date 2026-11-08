"""Comandos e publicação atômica com processos injetados."""

import json
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from dlpdownloader.modelos.erros import Cancelado, ErroDestino, ErroDownload
from dlpdownloader.servicos.yt_dlp import ServicoDownload, montar_comando


def executor_falso(comandos):
    def executar(comando, cancelar, receber):
        comandos.append(comando)
        if "--print" in comando:
            destino = Path(comando[comando.index("-P") + 1])
            template = comando[comando.index("-o") + 1]
            pasta = destino / Path(template).parent
            arquivo = pasta / "Título [id].m4a"
            arquivo.write_bytes(b"audio-ou-video")
            receber("DLP_RESULT:" + json.dumps(str(arquivo)))
        else:
            Path(comando[-1]).write_bytes(b"audio-convertido")

    return executar


def test_comando_preserva_url_e_destino_sem_shell(pedido, ferramentas):
    comando = montar_comando(pedido, ferramentas, pedido.destino / ".dlp-teste")
    assert comando[-2:] == ["--", pedido.url]
    assert comando[comando.index("-P") + 1] == str(pedido.destino)
    assert comando[0] == str(ferramentas.yt_dlp)
    assert "--ignore-config" in comando
    assert "--progress-template" in comando


def test_arquivo_publicado_e_staging_removido(pedido, ferramentas):
    comandos = []
    resultado = ServicoDownload(ferramentas, executor_falso(comandos)).baixar(
        pedido, threading.Event(), lambda evento: None
    )
    assert resultado.read_bytes() == b"audio-ou-video"
    assert list(pedido.destino.iterdir()) == [resultado]


def test_arquivo_existente_preservado(pedido, ferramentas):
    final = pedido.destino / "Título [id].m4a"
    final.write_bytes(b"original")
    with pytest.raises(ErroDestino):
        ServicoDownload(ferramentas, executor_falso([])).baixar(
            pedido, threading.Event(), lambda evento: None
        )
    assert final.read_bytes() == b"original"


def test_bitrate_explicito_realmente_invoca_encoder(pedido, ferramentas):
    comandos = []
    pedido = replace(pedido, perfil="m4a", bitrate=192)
    resultado = ServicoDownload(ferramentas, executor_falso(comandos)).baixar(
        pedido, threading.Event(), lambda evento: None
    )
    assert len(comandos) == 2
    assert comandos[1][comandos[1].index("-c:a") + 1] == "aac"
    assert comandos[1][comandos[1].index("-b:a") + 1] == "192k"
    assert resultado.name.endswith("192k.m4a")


def test_ausencia_de_resultado_nao_vira_sucesso(pedido, ferramentas):
    with pytest.raises(ErroDownload):
        ServicoDownload(ferramentas, lambda *args: None).baixar(
            pedido, threading.Event(), lambda evento: None
        )
    assert not list(pedido.destino.iterdir())


def test_resultado_fora_do_staging_rejeitado(pedido, ferramentas, tmp_path):
    externo = tmp_path / "externo.mp4"
    externo.write_bytes(b"x")

    def executar(comando, cancelar, receber):
        receber("DLP_RESULT:" + json.dumps(str(externo)))

    with pytest.raises(ErroDownload):
        ServicoDownload(ferramentas, executar).baixar(pedido, threading.Event(), lambda e: None)
    assert externo.read_bytes() == b"x"


def test_cancelamento_nao_publica(pedido, ferramentas):
    cancelamento = threading.Event()
    falso = executor_falso([])

    def executar(comando, cancelar, receber):
        falso(comando, cancelar, receber)
        cancelar.set()

    with pytest.raises(Cancelado):
        ServicoDownload(ferramentas, executar).baixar(pedido, cancelamento, lambda e: None)
    assert not list(pedido.destino.iterdir())
