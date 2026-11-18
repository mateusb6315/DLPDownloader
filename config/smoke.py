"""Diagnóstico de mídia sintética para a distribuição congelada."""

import functools
import http.server
import subprocess
import threading
from pathlib import Path

from services._infra.arquivos import gravar_json
from services._infra.dependencias import verificar
from services._models.download import SolicitacaoDownload
from services._models.erros import Cancelado, SubstituicaoRecusada
from services.downloader import ServicoDownload

PERFIS_TESTE = (
    ("mp4", None, ".mp4"),
    ("mkv", None, ".mkv"),
    ("original", None, ".m4a"),
    ("mp3", 192, ".mp3"),
    ("m4a", 192, ".m4a"),
    ("opus", 128, ".opus"),
    ("flac", None, ".flac"),
    ("wav", None, ".wav"),
)


class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _gerar_fonte(ffmpeg: Path, fonte: Path) -> None:
    subprocess.run(
        [
            str(ffmpeg),
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
        ],
        check=True,
        capture_output=True,
        timeout=30,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _verificar_substituicao_e_cancelamento(servico, pedido, final) -> None:
    original = final.read_bytes()
    try:
        servico.baixar(pedido, threading.Event(), lambda _: None)
    except SubstituicaoRecusada:
        if final.read_bytes() != original:
            raise RuntimeError("Arquivo original alterado.") from None
    else:
        raise RuntimeError("Substituição sem confirmação.")

    cancelar = threading.Event()
    cancelar.set()
    try:
        servico.baixar(pedido, cancelar, lambda _: None)
    except Cancelado:
        return
    raise RuntimeError("Cancelamento não respeitado.")


def testar_midia(raiz: Path, dados: Path) -> None:
    """Exercita os perfis com as ferramentas portáteis e um servidor localhost."""
    dados = dados.resolve()
    dados.mkdir(parents=True, exist_ok=True)
    ferramentas = verificar(raiz, threading.Event())
    _gerar_fonte(ferramentas.ffmpeg, dados / "fonte.mp4")
    handler = functools.partial(_Handler, directory=str(dados))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as servidor:
        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        try:
            servico = ServicoDownload(ferramentas)
            url = f"http://127.0.0.1:{servidor.server_port}/fonte.mp4"
            resultados = []
            for perfil, bitrate, extensao in PERFIS_TESTE:
                destino = dados / perfil
                destino.mkdir()
                pedido = SolicitacaoDownload(url, perfil, bitrate, destino)
                eventos = []
                final = servico.baixar(pedido, threading.Event(), eventos.append)
                if (
                    final.suffix != extensao
                    or not final.stat().st_size
                    or not eventos
                    or list(destino.glob(".dlp-*"))
                ):
                    raise RuntimeError("Diagnóstico de mídia incompleto.")
                resultados.append(perfil)
            _verificar_substituicao_e_cancelamento(servico, pedido, final)
        finally:
            servidor.shutdown()
            thread.join(timeout=5)
    gravar_json(dados / "resultado.json", {"perfis": resultados, "sucesso": True})


def verificar_midia(raiz: Path, dados: Path) -> int:
    """Registra o resultado sem expor URLs ou a saída bruta das ferramentas."""
    try:
        testar_midia(raiz, dados)
    except Exception as erro:
        try:
            gravar_json(dados / "resultado.json", {"sucesso": False, "erro": type(erro).__name__})
        except OSError:
            pass
        return 1
    return 0
