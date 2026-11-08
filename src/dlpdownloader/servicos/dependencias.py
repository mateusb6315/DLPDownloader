"""Localização e verificação das ferramentas descritas no manifesto."""

import hashlib
import json
import threading
from dataclasses import dataclass
from pathlib import Path

from dlpdownloader.modelos.erros import ErroDependencia
from dlpdownloader.servicos.processos import executar


@dataclass(frozen=True)
class Ferramentas:
    """Executáveis absolutos usados pelo serviço de download."""

    yt_dlp: Path
    ffmpeg: Path
    ffprobe: Path
    deno: Path


def localizar(raiz: Path) -> Ferramentas:
    """Exige o conjunto local; nunca procura ferramentas no PATH."""
    base = raiz / "vendor"
    ferramentas = Ferramentas(
        base / "yt-dlp/yt-dlp.exe",
        base / "ffmpeg/ffmpeg.exe",
        base / "ffmpeg/ffprobe.exe",
        base / "deno/deno.exe",
    )
    for caminho in vars(ferramentas).values():
        if not caminho.is_file():
            raise ErroDependencia(f"Ferramenta ausente: {caminho.name}. Prepare vendor/.")
    return ferramentas


def verificar(raiz: Path, cancelamento: threading.Event) -> Ferramentas:
    """Valida hashes instalados e inicia cada ferramenta com prazo limitado."""
    ferramentas = localizar(raiz)
    try:
        instaladas = json.loads((raiz / "vendor/installed.json").read_text(encoding="utf-8"))
        manifesto = hashlib.sha256((raiz / "vendor/manifest.json").read_bytes()).hexdigest()
        if instaladas["manifesto_sha256"] != manifesto:
            raise ErroDependencia("O manifesto mudou. Prepare vendor/ novamente.")
        for caminho in vars(ferramentas).values():
            relativo = caminho.relative_to(raiz / "vendor").as_posix()
            esperado = instaladas["arquivos"][relativo]
            with caminho.open("rb") as arquivo:
                real = hashlib.file_digest(arquivo, "sha256").hexdigest()
            if real != esperado:
                raise ErroDependencia(f"Integridade inválida: {caminho.name}. Prepare vendor/.")
        for caminho in vars(ferramentas).values():
            flag = (
                "-version" if caminho in {ferramentas.ffmpeg, ferramentas.ffprobe} else "--version"
            )
            executar([str(caminho), flag], cancelamento, lambda linha: None, limite=20)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        raise ErroDependencia(
            "Instalação portátil incompleta. Prepare vendor/ novamente."
        ) from erro
    return ferramentas
