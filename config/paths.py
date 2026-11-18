"""Resolve recursos empacotados, ferramentas externas e dados por usuário."""

import os
import sys
from pathlib import Path


def em_distribuicao() -> bool:
    """Reconhece uma distribuição gerada pelo Nuitka."""
    return bool(getattr(globals().get("__compiled__"), "standalone", False))


def raiz_projeto() -> Path:
    """Retorna a raiz externa, independente do diretório de trabalho."""
    if em_distribuicao():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def diretorio_dados() -> Path:
    """Retorna o destino gravável de configurações e logs."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "DLPDownloader"


def caminho_icone() -> Path:
    """Localiza o PNG dentro do pacote, inclusive quando congelado."""
    return Path(__file__).resolve().parents[1] / "ui" / "resources" / "flet.png"
