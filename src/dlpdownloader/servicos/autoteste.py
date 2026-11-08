"""Diagnóstico de mídia local para validar a distribuição congelada na compilação."""

import functools
import http.server
import subprocess
import threading
from pathlib import Path

from dlpdownloader.modelos.download import SolicitacaoDownload
from dlpdownloader.modelos.erros import Cancelado, SubstituicaoRecusada
from dlpdownloader.servicos.arquivos import gravar_json
from dlpdownloader.servicos.dependencias import verificar
from dlpdownloader.servicos.yt_dlp import ServicoDownload


def testar_midia(raiz: Path, dados: Path) -> None:
    """Exercita os perfis sem internet ou ferramentas globais; não registra saída bruta."""
    dados.mkdir(parents=True, exist_ok=True)
    ferramentas = verificar(raiz, threading.Event())
    fonte = dados / "fonte.mp4"
    comando = [
        str(ferramentas.ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
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
    ]
    subprocess.run(comando, check=True, capture_output=True, timeout=30)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    servidor = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=str(dados))
    )
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    resultados = []
    try:
        servico = ServicoDownload(ferramentas)
        for perfil, bitrate in [
            ("mp4", None),
            ("mkv", None),
            ("original", None),
            ("mp3", 192),
            ("m4a", 192),
            ("opus", 128),
            ("flac", None),
            ("wav", None),
        ]:
            destino = dados / perfil
            destino.mkdir()
            pedido = SolicitacaoDownload(
                f"http://127.0.0.1:{servidor.server_port}/fonte.mp4", perfil, bitrate, destino
            )
            eventos = []
            final = servico.baixar(pedido, threading.Event(), eventos.append)
            if not final.stat().st_size or not eventos or list(destino.glob(".dlp-*")):
                raise RuntimeError("Diagnóstico de mídia incompleto.")
            resultados.append(perfil)
        original = final.read_bytes()
        try:
            servico.baixar(pedido, threading.Event(), lambda e: None)
        except SubstituicaoRecusada:
            if final.read_bytes() != original:
                raise RuntimeError("Arquivo original alterado.") from None
        else:
            raise RuntimeError("Substituição sem confirmação.")
        cancelar = threading.Event()
        cancelar.set()
        try:
            servico.baixar(pedido, cancelar, lambda e: None)
        except Cancelado:
            pass
        else:
            raise RuntimeError("Cancelamento não respeitado.")
        gravar_json(dados / "resultado.json", {"perfis": resultados, "sucesso": True})
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=5)
