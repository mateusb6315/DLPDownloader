"""Seleciona os arquivos de ferramentas que fazem parte da distribuição."""

import shutil
from pathlib import Path

from services._infra.manifesto import arquivos_previstos, ler_manifesto


def copiar_vendor(origem: Path, destino: Path) -> None:
    """Não transporta caches, ferramentas antigas ou arquivos não declarados."""
    manifesto = ler_manifesto(origem)
    arquivos = [*arquivos_previstos(manifesto), "manifest.json", "installed.json"]
    arquivos += [
        p.relative_to(origem).as_posix() for p in (origem / "licenses").rglob("*") if p.is_file()
    ]
    for relativo in arquivos:
        arquivo = origem / relativo
        if arquivo.is_symlink():
            raise ValueError(f"Link não permitido no pacote: {relativo}")
        final = destino / relativo
        final.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arquivo, final)
