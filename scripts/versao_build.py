"""Incorpora a versão da distribuição no executável, sem arquivo externo."""

import re
import tomllib
from pathlib import Path

FORMATO_VERSAO = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def solicitar_versao() -> str:
    """Solicita uma versão com três componentes numéricos."""
    mensagem = "Digite a próxima versão: "
    while True:
        versao = input(mensagem).strip()
        if FORMATO_VERSAO.fullmatch(versao):
            return versao
        mensagem = "Formato inválido. Informe X.Y.Z: "


def versao_base(raiz: Path, nome: str, beta: bool) -> str:
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
    if not isinstance(versao, str) or not FORMATO_VERSAO.fullmatch(versao):
        raise ValueError("A versão deve conter três componentes numéricos no formato X.Y.Z.")
    return versao


def preparar_versao(raiz: Path, temporario: Path, nome: str, beta: bool) -> None:
    versao = versao_base(raiz, nome, beta)
    (temporario / "versao_build.py").write_text(
        f"VERSAO = {versao!r}\nBETA = {beta!r}\n", encoding="utf-8"
    )
