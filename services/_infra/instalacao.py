"""Troca conjuntos completos com recuperação de falhas de instalação."""

import os
import shutil
import uuid
from pathlib import Path


def instalar_conjunto(
    vendor: Path, staging: Path, backup: Path, manifesto: dict, trocar_manifesto: bool = False
) -> None:
    """Metadados ficam ausentes durante a troca; backup é restaurado em erro."""
    backup.mkdir()
    # Preservar avisos particulares; descartar somente avisos do FFmpeg substituído.
    licencas = vendor / "licenses"
    if licencas.exists():
        for origem in licencas.iterdir():
            if origem.is_file() and not origem.name.casefold().startswith("ffmpeg-"):
                destino = staging / "licenses" / origem.name
                if not destino.exists():
                    shutil.copy2(origem, destino)
    nomes = ["installed.json", *(f["nome"] for f in manifesto["ferramentas"]), "licenses"]
    if trocar_manifesto:
        nomes.append("manifest.json")
    salvos, instalados = [], []
    try:
        for nome in nomes:
            destino = vendor / nome
            if destino.exists():
                os.replace(destino, backup / nome)
                salvos.append(nome)
            if nome != "installed.json":
                os.replace(staging / nome, destino)
                instalados.append(nome)
        os.replace(staging / "installed.json", vendor / "installed.json")
        instalados.append("installed.json")
    except BaseException:
        try:
            for nome in reversed(instalados):
                destino = vendor / nome
                if destino.is_dir():
                    shutil.rmtree(destino)
                else:
                    destino.unlink()
            for nome in reversed(salvos):
                os.replace(backup / nome, vendor / nome)
        except OSError as erro:
            recuperacao = vendor.parent / f".recuperacao-{uuid.uuid4().hex}"
            backup.rename(recuperacao)
            raise RuntimeError(f"Recuperação manual necessária: {recuperacao}") from erro
        raise
