"""Contrato público da nova fachada, com processos e mídia reais."""

import functools
import http.server
import json
import subprocess
import threading
from pathlib import Path

import pytest

from services._infra.dependencias import localizar
from services._models.download import SolicitacaoDownload
from services._models.erros import Cancelado, ErroDownload, SubstituicaoRecusada
from services.downloader import ServicoDownload

pytestmark = pytest.mark.externo


@pytest.fixture(scope="module")
def midia(tmp_path_factory):
    ferramentas = localizar(Path(__file__).resolve().parents[1])
    pasta = tmp_path_factory.mktemp("midia")
    fonte = pasta / "fonte.mp4"
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
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "1",
            "-c:v",
            "mpeg4",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(fonte),
        ],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    subprocess.run(
        [
            str(ferramentas.ffmpeg),
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(fonte),
            "-map",
            "0:v",
            "-map",
            "0:a",
            "-c",
            "copy",
            "-f",
            "dash",
            str(pasta / "manifest.mpd"),
        ],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        cwd=pasta,
    )
    # Entradas adicionais exercitam contêineres, codecs e HLS sem libx264.
    for nome, argumentos in [
        ("fonte.webm", ["-c:v", "libvpx-vp9", "-c:a", "libopus"]),
        ("h264.mp4", ["-vf", "scale=160:96", "-c:v", "libopenh264", "-c:a", "aac"]),
        ("hevc.mp4", ["-vf", "scale=160:96", "-c:v", "libkvazaar", "-c:a", "aac"]),
        ("av1.webm", ["-c:v", "libaom-av1", "-cpu-used", "8", "-c:a", "libopus"]),
        ("fonte.ogg", ["-vn", "-c:a", "libvorbis"]),
        ("fonte.m3u8", ["-vn", "-c:a", "aac", "-f", "hls", "-hls_time", "1"]),
    ]:
        subprocess.run(
            [
                str(ferramentas.ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-i",
                str(fonte),
                *argumentos,
                str(pasta / nome),
            ],
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    (pasta / "invalido.mp4").write_bytes(b"midia invalida" * 8192)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(pasta))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield ferramentas, f"http://127.0.0.1:{servidor.server_port}/fonte.mp4"
    servidor.shutdown()
    servidor.server_close()
    thread.join(timeout=5)


@pytest.mark.parametrize("perfil", ["mp4", "mkv"])
def test_video_real_publicado_com_audio_e_progresso(midia, tmp_path, perfil):
    ferramentas, url = midia
    pedido = SolicitacaoDownload(url, perfil, None, tmp_path)
    eventos = []
    resultado = ServicoDownload(ferramentas).baixar(pedido, threading.Event(), eventos.append)
    assert resultado.suffix == f".{perfil}"
    dados = json.loads(
        subprocess.check_output(
            [
                str(ferramentas.ffprobe),
                "-v",
                "error",
                "-show_streams",
                "-of",
                "json",
                str(resultado),
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    )
    assert {s["codec_type"] for s in dados["streams"]} == {"video", "audio"}
    assert any(e.etapa == "baixando" for e in eventos)
    assert list(tmp_path.iterdir()) == [resultado]


@pytest.mark.parametrize("perfil", ["mp4", "mkv"])
def test_junta_duas_faixas_reais(midia, tmp_path, perfil):
    ferramentas, url = midia
    pedido = SolicitacaoDownload(url.replace("fonte.mp4", "manifest.mpd"), perfil, None, tmp_path)
    eventos = []
    resultado = ServicoDownload(ferramentas).baixar(pedido, threading.Event(), eventos.append)
    assert len({e.faixa for e in eventos if e.etapa == "baixando"}) == 2
    dados = json.loads(
        subprocess.check_output(
            [
                str(ferramentas.ffprobe),
                "-v",
                "error",
                "-show_streams",
                "-of",
                "json",
                str(resultado),
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    )
    assert {s["codec_type"] for s in dados["streams"]} == {"video", "audio"}
    assert list(tmp_path.iterdir()) == [resultado]


def test_recusa_preserva_e_confirmacao_substitui(midia, tmp_path):
    ferramentas, url = midia
    pedido = SolicitacaoDownload(url, "mp4", None, tmp_path)
    servico = ServicoDownload(ferramentas)
    resultado = servico.baixar(pedido, threading.Event(), lambda e: None)
    original = resultado.read_bytes()
    resultado.write_bytes(b"arquivo anterior")
    with pytest.raises(SubstituicaoRecusada):
        servico.baixar(pedido, threading.Event(), lambda e: None)
    assert resultado.read_bytes() == b"arquivo anterior"
    assert list(tmp_path.iterdir()) == [resultado]
    confirmado = servico.baixar(pedido, threading.Event(), lambda e: None, lambda: True)
    assert confirmado == resultado
    assert resultado.read_bytes() == original
    assert list(tmp_path.iterdir()) == [resultado]


def test_cancelamento_durante_progresso_nao_publica(midia, tmp_path):
    ferramentas, url = midia
    pedido = SolicitacaoDownload(url, "mkv", None, tmp_path)
    cancelamento = threading.Event()
    eventos = []

    def receber(evento):
        eventos.append(evento)
        cancelamento.set()

    with pytest.raises(Cancelado):
        ServicoDownload(ferramentas).baixar(pedido, cancelamento, receber)
    assert eventos
    assert not list(tmp_path.iterdir())


def test_falha_de_remux_apos_progresso_nao_publica(midia, tmp_path):
    ferramentas, url = midia
    pedido = SolicitacaoDownload(url.replace("fonte.mp4", "invalido.mp4"), "mkv", None, tmp_path)
    eventos = []
    with pytest.raises(ErroDownload):
        ServicoDownload(ferramentas).baixar(pedido, threading.Event(), eventos.append)
    assert any(e.etapa == "baixando" for e in eventos)
    assert not list(tmp_path.iterdir())
