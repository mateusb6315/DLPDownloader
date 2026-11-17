"""Pequenos contratos de CLI, caminhos e ambiente de compilação."""

import os
import re
import sys
from pathlib import Path

from services._infra.bloqueios import bloqueio as bloqueio

RAIZ = Path(__file__).resolve().parents[1]


def status(mensagem: str) -> None:
    """Emite uma etapa de compilação com flush imediato."""
    texto = f"[compilação] {mensagem}"
    codificacao = sys.stdout.encoding or "utf-8"
    print(texto.encode(codificacao, errors="backslashreplace").decode(codificacao), flush=True)


def ambiente_compilacao() -> dict[str, str]:
    """Evita coletar DLLs incompatíveis de Git, Poppler ou outro software no PATH."""
    import PyQt6

    ambiente = dict(os.environ)
    windows = Path(ambiente.get("SystemRoot", r"C:\Windows"))
    caminhos = [
        Path(PyQt6.__file__).parent / "Qt6/bin",
        Path(sys.executable).parent,
        Path(sys.base_prefix),
        windows / "System32",
        windows,
    ]
    ambiente["PATH"] = os.pathsep.join(map(str, caminhos))
    for nome in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH", "PYTHONHOME"):
        ambiente.pop(nome, None)
    return ambiente


def validar_nome(nome: str) -> str:
    """Aceita nomes livres que possam ser usados como parte de arquivo Windows."""
    if not nome or nome != nome.strip() or nome.endswith("."):
        raise ValueError("Informe um nome não vazio, sem espaços nas extremidades ou ponto final.")
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', nome):
        raise ValueError("O nome contém caracteres não permitidos no Windows.")
    return nome
