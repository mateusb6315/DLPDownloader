"""Resolve recursos empacotados, ferramentas externas e dados por usuário."""

import os
import sys
from pathlib import Path


def raiz_projeto() -> Path:
    """Retorna a raiz externa, independente do diretório de trabalho."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def diretorio_dados() -> Path:
    """Retorna o destino gravável de configurações e logs."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "DLPDownloader"


def caminho_icone() -> Path:
    """Localiza o PNG dentro do pacote, inclusive quando congelado."""
    return Path(__file__).resolve().parents[1] / "recursos" / "flet.png"
