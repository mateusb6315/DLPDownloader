"""Consulta releases estáveis para a versão base da distribuição."""

import json
from threading import Event
from time import monotonic
from urllib.request import Request, urlopen

from services._models.atualizacoes import (
    ReleaseEstavel,
    ResultadoConsulta,
    VersaoDistribuicao,
    normalizar_versao,
)
from services._models.erros import Cancelado, ErroAplicacao

REPOSITORIO = "mateusb6315/DLPDownloader"
API = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
LIMITE = 1_000_000
TIMEOUT = 5


def verificar_atualizacao(
    versao: VersaoDistribuicao | None, cancelamento: Event, *, abrir=urlopen
) -> ResultadoConsulta:
    """Oferece uma estável mais recente ou com a mesma versão base da beta."""
    if cancelamento.is_set():
        raise Cancelado()
    if versao is None:
        raise ErroAplicacao(
            "Desenvolvimento (sem versão de build). "
            "Use uma distribuição compilada para verificar atualizações."
        )
    local = normalizar_versao(versao.numero)
    remota, release = _consultar_release(cancelamento, abrir)
    disponivel = remota > local or (versao.beta and remota == local)
    return ResultadoConsulta(str(versao), release if disponivel else None)


def _consultar_release(cancelamento: Event, abrir) -> tuple[tuple[int, int, int], ReleaseEstavel]:
    pedido = Request(
        API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "DLPDownloader",
        },
    )
    try:
        prazo = monotonic() + TIMEOUT
        with abrir(pedido, timeout=TIMEOUT) as resposta:
            if resposta.status != 200:
                raise ValueError("Status HTTP inválido.")
            release = json.loads(_ler_resposta(resposta, cancelamento, prazo))
        tag = release["tag_name"]
        numero = normalizar_versao(tag.removeprefix("v"))
        url = release["html_url"]
        if (
            url != f"https://github.com/{REPOSITORIO}/releases/tag/{tag}"
            or release["draft"] is not False
            or release["prerelease"] is not False
        ):
            raise ValueError("Release estável inválida.")
        return numero, ReleaseEstavel(".".join(map(str, numero)), url)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as erro:
        raise ErroAplicacao(
            "Não foi possível verificar se há atualizações. Tente novamente mais tarde."
        ) from erro


def _ler_resposta(resposta, cancelamento: Event, prazo: float) -> bytearray:
    dados = bytearray()
    while len(dados) <= LIMITE:
        if cancelamento.is_set():
            raise Cancelado()
        if monotonic() >= prazo:
            raise TimeoutError()
        bloco = resposta.read1(min(65_536, LIMITE + 1 - len(dados)))
        if not bloco:
            return dados
        dados.extend(bloco)
    raise ValueError("Resposta excessiva.")
