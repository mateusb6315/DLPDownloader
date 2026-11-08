"""Obtém versões fixadas das ferramentas portáteis e verifica SHA-256."""

import argparse
import shutil
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dlpdownloader.servicos.manifesto import (
    arquivos_previstos,
    ler_manifesto,
    relativo_seguro,
    sha256,
)
from scripts.comum import RAIZ, bloqueio
from scripts.instalar_ferramentas import instalar_conjunto


def baixar(url: str, destino: Path) -> None:
    """Faz download por streaming, com prazo por leitura e arquivo temporário."""
    requisicao = urllib.request.Request(url, headers={"User-Agent": "DLPDownloader"})
    with urllib.request.urlopen(requisicao, timeout=60) as resposta, destino.open("wb") as saida:
        shutil.copyfileobj(resposta, saida)


def extrair(origem: Path, ferramenta: dict, staging: Path) -> None:
    """Extrai apenas arquivos esperados e licenças; nunca usa extractall."""
    for nome, destino in ferramenta["arquivos"].items():
        relativo_seguro(nome)
        relativo_seguro(destino)
    real = sha256(origem)
    if real != ferramenta["sha256"]:
        raise ValueError(f"SHA-256 inválido: {ferramenta['nome']}. Manifesto preservado.")
    if origem.suffix != ".zip":
        destino = staging / next(iter(ferramenta["arquivos"].values()))
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)
        return
    with zipfile.ZipFile(origem) as pacote:
        for nome, relativo in ferramenta["arquivos"].items():
            membros = [m for m in pacote.namelist() if Path(m).name == nome]
            if len(membros) != 1:
                raise ValueError(f"Arquivo ausente ou ambíguo no ZIP: {nome}")
            destino = staging / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            with pacote.open(membros[0]) as entrada, destino.open("wb") as saida:
                shutil.copyfileobj(entrada, saida)
        for membro in pacote.namelist():
            nome = Path(membro).name
            if nome.lower().startswith(("license", "copying")) and not membro.endswith("/"):
                destino = staging / "licenses" / f"{ferramenta['nome']}-{nome}"
                destino.parent.mkdir(exist_ok=True)
                destino.write_bytes(pacote.read(membro))


def preparar(
    raiz: Path = RAIZ,
    obter=baixar,
    manifesto_confiavel: Path | None = None,
    antes_de_instalar=None,
) -> None:
    """Prepara o conjunto completo antes de substituir a instalação anterior."""
    from dlpdownloader.servicos.arquivos import gravar_json

    vendor = raiz / "vendor"
    fonte = manifesto_confiavel or vendor / "manifest.json"
    manifesto = ler_manifesto(fonte.parent)
    with (
        bloqueio(raiz / ".preparacao.lock"),
        tempfile.TemporaryDirectory(prefix=".ferramentas-", dir=raiz) as pasta,
    ):
        trabalho = Path(pasta)
        staging = trabalho / "vendor"
        staging.mkdir()
        for ferramenta in manifesto["ferramentas"]:
            print(f"Preparando {ferramenta['nome']} {ferramenta['versao']}…", flush=True)
            extensao = ".zip" if ferramenta["url"].endswith(".zip") else ".exe"
            arquivo = trabalho / f"{ferramenta['nome']}{extensao}"
            obter(ferramenta["url"], arquivo)
            extrair(arquivo, ferramenta, staging)
        licencas = {
            "ffmpeg-COPYING.GPLv3.txt": "https://www.gnu.org/licenses/gpl-3.0.txt",
            "yt-dlp-LICENSE.txt": "https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.10.26/LICENSE",
            "deno-LICENSE.md": "https://raw.githubusercontent.com/denoland/deno/v2.9.8/LICENSE.md",
        }
        (staging / "licenses").mkdir(exist_ok=True)
        if manifesto_confiavel:
            aviso = manifesto_confiavel.parent / "licenses/README.md"
            if aviso.is_file():
                shutil.copy2(aviso, staging / "licenses/README.md")
        for nome, url in licencas.items():
            obter(url, staging / "licenses" / nome)
        hashes = {
            relativo: sha256(staging / relativo) for relativo in arquivos_previstos(manifesto)
        }
        metadados = {
            "manifesto_sha256": sha256(fonte),
            "arquivos": hashes,
        }
        gravar_json(staging / "installed.json", metadados)
        shutil.copy2(fonte, staging / "manifest.json")
        from dlpdownloader.servicos.dependencias import verificar

        verificar(trabalho, threading.Event())
        if antes_de_instalar:
            antes_de_instalar()
        instalar_conjunto(
            vendor,
            staging,
            trabalho / "backup",
            manifesto,
            trocar_manifesto=manifesto_confiavel is not None,
        )
    print("Ferramentas portáteis preparadas.", flush=True)


def main() -> int:
    """CLI de preparação explícita; nenhuma atualização ocorre ao abrir a GUI."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        preparar()
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
