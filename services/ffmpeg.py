"""Conversão direta de áudio com bitrate explícito, independente do yt-dlp."""

from pathlib import Path

from services._infra.processos import executar
from services._models.erros import ErroDownload
from services._models.progresso import EventoProgresso


def converter(
    pedido, origem, ferramentas, cancelamento, progresso, executar_processo=executar
) -> Path:
    progresso(EventoProgresso("finalizando"))
    destino = origem.with_name(f"{origem.stem} - {pedido.bitrate}k.{pedido.perfil}")
    codecs = {"mp3": "libmp3lame", "m4a": "aac", "opus": "libopus"}
    comando = [
        str(ferramentas.ffmpeg),
        "-hide_banner",
        "-nostdin",
        "-n",
        "-i",
        str(origem),
        "-vn",
        "-c:a",
        codecs[pedido.perfil],
        "-b:a",
        f"{pedido.bitrate}k",
        str(destino),
    ]
    executar_processo(comando, cancelamento, lambda linha: None)
    if not destino.is_file() or not destino.stat().st_size:
        raise ErroDownload("O FFmpeg não confirmou o áudio convertido.")
    return destino
