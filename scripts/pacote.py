"""Seleção explícita e medição do conteúdo distribuído."""

import importlib.metadata
import shutil
import sys
from pathlib import Path

from dlpdownloader.servicos.manifesto import arquivos_previstos, ler_manifesto


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


def medir_pacote(pacote: Path, versao: str) -> dict:
    """Tamanhos em bytes, versões e maiores arquivos para comparação de builds."""
    arquivos = [p for p in pacote.rglob("*") if p.is_file()]
    grupos = {}
    for arquivo in arquivos:
        relativo = arquivo.relative_to(pacote)
        grupo = "/".join(relativo.parts[:2]) if relativo.parts[0] == "vendor" else relativo.parts[0]
        grupos[grupo] = grupos.get(grupo, 0) + arquivo.stat().st_size
    return {
        "versao_pacote": versao,
        "bytes": sum(p.stat().st_size for p in arquivos),
        "quantidade_arquivos": len(arquivos),
        "componentes": grupos,
        "maiores_arquivos": [
            {"arquivo": p.relative_to(pacote).as_posix(), "bytes": p.stat().st_size}
            for p in sorted(arquivos, key=lambda p: p.stat().st_size, reverse=True)[:15]
        ],
        "ambiente": {
            "Python": sys.version.split()[0],
            **{n: importlib.metadata.version(n) for n in ("PyInstaller", "PyQt6")},
        },
    }
