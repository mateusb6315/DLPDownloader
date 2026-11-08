"""Localização e verificação das ferramentas descritas no manifesto."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path

from dlpdownloader.modelos.erros import ErroDependencia
from dlpdownloader.servicos.manifesto import arquivos_previstos, ler_manifesto, sha256
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
            raise ErroDependencia(f"Ferramenta ausente: {caminho.name}. Execute vendor/repair.exe.")
    return ferramentas


def verificar(raiz: Path, cancelamento: threading.Event) -> Ferramentas:
    """Valida hashes instalados e inicia cada ferramenta com prazo limitado."""
    ferramentas = localizar(raiz)
    try:
        instaladas = json.loads((raiz / "vendor/installed.json").read_text(encoding="utf-8"))
        contrato = ler_manifesto(raiz / "vendor")
        manifesto = sha256(raiz / "vendor/manifest.json", cancelamento)
        if instaladas["manifesto_sha256"] != manifesto:
            raise ErroDependencia("O manifesto mudou. Execute vendor/repair.exe.")
        previstos = arquivos_previstos(contrato)
        if set(instaladas["arquivos"]) != set(previstos):
            raise ErroDependencia("Lista de binários incompleta. Execute vendor/repair.exe.")
        for relativo in previstos:
            caminho = raiz / "vendor" / relativo
            if not caminho.is_file():
                raise ErroDependencia(
                    f"Binário ausente: {caminho.name}. Execute vendor/repair.exe."
                )
            if sha256(caminho, cancelamento) != instaladas["arquivos"][relativo]:
                raise ErroDependencia(
                    f"Integridade inválida: {caminho.name}. Execute vendor/repair.exe."
                )
        for caminho in vars(ferramentas).values():
            flag = (
                "-version" if caminho in {ferramentas.ffmpeg, ferramentas.ffprobe} else "--version"
            )
            executar([str(caminho), flag], cancelamento, lambda linha: None, limite=20)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        raise ErroDependencia(
            "Instalação portátil incompleta. Execute vendor/repair.exe."
        ) from erro
    return ferramentas
