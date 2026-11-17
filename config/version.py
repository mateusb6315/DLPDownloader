"""Identifica a versão base e o canal da distribuição desktop."""

import json

from config.paths import em_distribuicao, raiz_projeto
from services._models.atualizacoes import VersaoDistribuicao, normalizar_versao
from services._models.erros import ErroAplicacao

LIMITE_JSON = 4096
ERRO_VERSAO = (
    "Não foi possível verificar a versão atual do DLP Downloader. "
    "Extraia ou instale novamente a distribuição e tente novamente."
)


def ler_versao_atual() -> VersaoDistribuicao | None:
    """Usa o módulo incorporado ao build, com fallback para pacotes antigos."""
    if not em_distribuicao():
        return None
    try:
        import versao_build
    except ModuleNotFoundError as erro:
        if erro.name != "versao_build":
            raise ErroAplicacao(ERRO_VERSAO) from erro
        return _ler_versao_antiga()
    try:
        normalizar_versao(versao_build.VERSAO)
        if not isinstance(versao_build.BETA, bool):
            raise ValueError("Canal inválido.")
        return VersaoDistribuicao(versao_build.VERSAO, versao_build.BETA)
    except (AttributeError, ValueError) as erro:
        raise ErroAplicacao(ERRO_VERSAO) from erro


def _ler_versao_antiga() -> VersaoDistribuicao:
    try:
        with (raiz_projeto() / "version.json").open("rb") as arquivo:
            conteudo = arquivo.read(LIMITE_JSON + 1)
        if len(conteudo) > LIMITE_JSON:
            raise ValueError("Arquivo excessivo.")
        dados = json.loads(conteudo.decode("utf-8"))
        numero = normalizar_versao(dados["version"])
        return VersaoDistribuicao(".".join(map(str, numero)))
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as erro:
        raise ErroAplicacao(ERRO_VERSAO) from erro
