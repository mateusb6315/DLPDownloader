"""Regras puras das versões estáveis publicadas."""

import re

from dlpdownloader.modelos.erros import ErroAplicacao


def normalizar_versao(valor: str) -> tuple[int, int, int]:
    if not isinstance(valor, str) or not re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+", valor):
        raise ErroAplicacao("A versão informada não possui um formato válido.")
    return tuple(map(int, valor.removeprefix("v").split(".")))
