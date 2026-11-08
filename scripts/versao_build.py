"""Incorpora a versão da distribuição no executável, sem arquivo externo."""

import re
import tomllib
from pathlib import Path


def preparar_versao(raiz: Path, temporario: Path, nome: str, beta: bool) -> None:
    """Usa versão numérica do nome beta ou a versão do projeto para nomes livres."""
    if beta:
        encontrado = re.match(r"^([0-9]+\.[0-9]+\.[0-9]+)(?:$|[^0-9.])", nome)
        if encontrado:
            versao = encontrado.group(1)
        else:
            with (raiz / "pyproject.toml").open("rb") as arquivo:
                versao = tomllib.load(arquivo)["project"]["version"]
    else:
        versao = nome
    if not isinstance(versao, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", versao):
        raise ValueError("A versão base do projeto deve conter três números.")
    (temporario / "versao_build.py").write_text(
        f"VERSAO = {versao!r}\nBETA = {beta!r}\n", encoding="utf-8"
    )
