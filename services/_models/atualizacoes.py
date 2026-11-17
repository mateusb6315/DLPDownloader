"""Versões da distribuição e resultados da consulta de releases."""

import re
from dataclasses import dataclass


def normalizar_versao(valor: str) -> tuple[int, int, int]:
    if not isinstance(valor, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", valor):
        raise ValueError("A versão deve conter três componentes numéricos.")
    maior, menor, correcao = map(int, valor.split("."))
    return maior, menor, correcao


@dataclass(frozen=True)
class VersaoDistribuicao:
    numero: str
    beta: bool = False

    def __str__(self) -> str:
        return f"{self.numero} (beta)" if self.beta else self.numero


@dataclass(frozen=True)
class ReleaseEstavel:
    versao: str
    url: str


@dataclass(frozen=True)
class ResultadoConsulta:
    versao_atual: str
    disponivel: ReleaseEstavel | None
