"""Identifica a build pelo JSON distribuído ao lado do executável."""

import json
import re
import sys
from pathlib import Path

from dlpdownloader.modelos.erros import ErroAplicacao

ERRO_VERSAO = (
    "Não foi possível verificar a versão atual do DLP Downloader. "
    "Verifique se version.json foi alterado ou está ausente no diretório e tente novamente."
)
DESENVOLVIMENTO = "Desenvolvimento (sem versão de build)"
LIMITE = 4096


def ler_versao(caminho: Path) -> str:
    """Lê e valida o arquivo; não consulta metadados instalados nem usa fallback."""
    try:
        with caminho.open("rb") as arquivo:
            conteudo = arquivo.read(LIMITE + 1)
        if len(conteudo) > LIMITE:
            raise ValueError("Arquivo excessivo")
        dados = json.loads(conteudo.decode("utf-8"))
        valor = dados["version"]
        if not isinstance(valor, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", valor):
            raise ValueError("Versão inválida")
        return ".".join(str(int(parte)) for parte in valor.split("."))
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as erro:
        raise ErroAplicacao(ERRO_VERSAO) from erro


def versao_atual() -> str | None:
    """None representa execução por fonte, sem versão de distribuição desktop."""
    if not getattr(sys, "frozen", False):
        return None
    try:
        import versao_build
    except ImportError:
        pass
    else:
        valor = versao_build.VERSAO
        if not isinstance(valor, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", valor):
            raise ErroAplicacao(ERRO_VERSAO)
        return valor
    return ler_versao(Path(sys.executable).resolve().parent / "version.json")


def build_beta() -> bool:
    """Identifica builds beta sem criar metadados externos."""
    if not getattr(sys, "frozen", False):
        return False
    try:
        import versao_build
    except ImportError:
        return False
    return versao_build.BETA is True
