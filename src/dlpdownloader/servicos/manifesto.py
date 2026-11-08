"""Contrato dos arquivos portáteis e leitura cancelável de sua integridade."""

import hashlib
import json
import re
import threading
from pathlib import Path, PurePosixPath, PureWindowsPath

from dlpdownloader.modelos.erros import Cancelado


def relativo_seguro(valor: str) -> str:
    """Aceita somente caminhos portáteis relativos, sem componentes especiais."""
    if not isinstance(valor, str) or not valor or "\\" in valor or ":" in valor:
        raise ValueError("Caminho inválido no manifesto.")
    if PureWindowsPath(valor).is_absolute() or PurePosixPath(valor).is_absolute():
        raise ValueError("Caminho absoluto no manifesto.")
    if any(p in {"", ".", ".."} for p in valor.split("/")):
        raise ValueError("Caminho inseguro no manifesto.")
    return valor


def ler_manifesto(vendor: Path) -> dict:
    """Valida nomes, hashes e destinos únicos antes de qualquer escrita."""
    dados = json.loads((vendor / "manifest.json").read_text(encoding="utf-8"))
    if (
        not isinstance(dados, dict)
        or not isinstance(dados.get("ferramentas"), list)
        or not dados["ferramentas"]
    ):
        raise ValueError("Manifesto sem ferramentas.")
    nomes, destinos = set(), set()
    for ferramenta in dados["ferramentas"]:
        if not isinstance(ferramenta, dict):
            raise ValueError("Ferramenta inválida no manifesto.")
        nome = ferramenta["nome"]
        if nome not in {"yt-dlp", "ffmpeg", "deno"} or nome in nomes:
            raise ValueError("Nome de ferramenta inválido ou repetido.")
        nomes.add(nome)
        if not re.fullmatch(r"[0-9a-f]{64}", ferramenta["sha256"]):
            raise ValueError("SHA-256 inválido no manifesto.")
        if not isinstance(ferramenta["arquivos"], dict) or not ferramenta["arquivos"]:
            raise ValueError("Ferramenta sem arquivos.")
        for origem, destino in ferramenta["arquivos"].items():
            if relativo_seguro(origem) != PurePosixPath(origem).name:
                raise ValueError("Origem deve ser um nome de arquivo.")
            relativo_seguro(destino)
            if not destino.startswith(nome + "/") or destino.casefold() in destinos:
                raise ValueError("Destino inválido ou repetido.")
            destinos.add(destino.casefold())
    obrigatorios = {"yt-dlp/yt-dlp.exe", "ffmpeg/ffmpeg.exe", "ffmpeg/ffprobe.exe", "deno/deno.exe"}
    if not obrigatorios.issubset(destinos):
        raise ValueError("Manifesto não declara todos os executáveis obrigatórios.")
    return dados


def arquivos_previstos(manifesto: dict) -> list[str]:
    """Lista completa de EXEs e DLLs necessários."""
    return [p for f in manifesto["ferramentas"] for p in f["arquivos"].values()]


def sha256(arquivo: Path, cancelar: threading.Event | None = None) -> str:
    """Evita bloquear o cancelamento durante leitura de binários grandes."""
    digest = hashlib.sha256()
    with arquivo.open("rb") as entrada:
        while True:
            if cancelar is not None and cancelar.is_set():
                raise Cancelado()
            bloco = entrada.read(1024 * 1024)
            if not bloco:
                return digest.hexdigest()
            digest.update(bloco)
