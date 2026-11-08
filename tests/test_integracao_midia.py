"""Ferramentas reais com mídia sintética servida somente em localhost."""

import functools
import http.server
import json
import subprocess
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from dlpdownloader.config.caminhos import raiz_projeto
from dlpdownloader.servicos.dependencias import localizar
from dlpdownloader.servicos.yt_dlp import ServicoDownload

pytestmark = pytest.mark.externo


@pytest.fixture(scope="module")
def midia(tmp_path_factory):
    ferramentas = localizar(raiz_projeto())
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
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(pasta))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield ferramentas, f"http://127.0.0.1:{servidor.server_port}/fonte.mp4"
    servidor.shutdown()
    servidor.server_close()
    thread.join(timeout=5)


@pytest.mark.parametrize(
    "perfil,bitrate,extensao",
    [
        ("mp4", None, ".mp4"),
        ("mkv", None, ".mkv"),
        ("original", None, ".m4a"),
        ("mp3", 192, ".mp3"),
        ("m4a", 192, ".m4a"),
        ("opus", 128, ".opus"),
        ("flac", None, ".flac"),
        ("wav", None, ".wav"),
    ],
)
def test_download_conversao_e_protocolo_reais(midia, pedido, perfil, bitrate, extensao):
    ferramentas, url = midia
    eventos = []
    pedido = replace(pedido, url=url, perfil=perfil, bitrate=bitrate)
    resultado = ServicoDownload(ferramentas).baixar(pedido, threading.Event(), eventos.append)
    assert resultado.suffix == extensao and resultado.stat().st_size > 0
    assert any(e.etapa == "baixando" for e in eventos)
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
    tipos = {stream["codec_type"] for stream in dados["streams"]}
    assert "audio" in tipos
    assert ("video" in tipos) == (perfil in {"mp4", "mkv"})
    assert not list(Path(pedido.destino).glob(".dlp-*"))


@pytest.mark.parametrize("perfil", ["mp4", "mkv"])
def test_juncao_real_de_video_e_audio_separados(midia, pedido, perfil):
    ferramentas, url = midia
    eventos = []
    pedido = replace(pedido, url=url.replace("fonte.mp4", "manifest.mpd"), perfil=perfil)
    resultado = ServicoDownload(ferramentas).baixar(pedido, threading.Event(), eventos.append)
    faixas = {evento.faixa for evento in eventos if evento.etapa == "baixando"}
    assert len(faixas) == 2
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
    assert {s["codec_type"] for s in dados["streams"]} == {"audio", "video"}


@pytest.mark.parametrize(
    "entrada,perfil,bitrate",
    [
        ("fonte.webm", "mkv", None),
        ("h264.mp4", "mp4", None),
        ("hevc.mp4", "mkv", None),
        ("av1.webm", "mkv", None),
        ("fonte.webm", "mp3", 192),
        ("fonte.webm", "flac", None),
        ("fonte.ogg", "opus", 128),
        ("fonte.m3u8", "m4a", 192),
    ],
)
def test_entradas_codecs_e_hls(midia, pedido, entrada, perfil, bitrate):
    ferramentas, url = midia
    pedido = replace(pedido, url=url.replace("fonte.mp4", entrada), perfil=perfil, bitrate=bitrate)
    resultado = ServicoDownload(ferramentas).baixar(pedido, threading.Event(), lambda e: None)
    assert resultado.stat().st_size > 0
    assert not list(pedido.destino.glob(".dlp-*"))
