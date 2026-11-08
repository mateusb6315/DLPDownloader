"""Compila o reparador portátil e incorpora uma cópia confiável do manifesto."""

import sys
from pathlib import Path


def compilar_repair(raiz: Path, temporario: Path, vendor: Path, executar_compilador, executar):
    """Não depende da pasta lib nem de ferramentas de mídia para iniciar."""
    dist = temporario / "repair-dist"
    comando = [
        sys.executable,
        "-u",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--noupx",
        "--name",
        "repair",
        "--paths",
        str(raiz / "src"),
        "--paths",
        str(raiz),
        "--distpath",
        str(dist),
        "--workpath",
        str(temporario / "repair-work"),
        "--specpath",
        str(temporario / "repair-spec"),
        "--add-data",
        f"{vendor / 'manifest.json'}:.",
        "--add-data",
        f"{vendor / 'licenses/README.md'}:licenses",
        str(raiz / "scripts/repair.py"),
    ]
    executar_compilador(comando, executar)
    executavel = dist / "repair.exe"
    if not executavel.is_file():
        raise RuntimeError("O compilador não gerou o reparador esperado.")
    executavel.replace(vendor / "repair.exe")
