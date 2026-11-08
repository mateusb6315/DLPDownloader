"""Consulta funcional da release estável do projeto, sem dependência de Qt."""

import json
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from dlpdownloader.modelos.atualizacoes import normalizar_versao
from dlpdownloader.modelos.erros import ErroAplicacao

API = "https://api.github.com/repos/mateusb6315/DLPDownloader/releases/latest"
LIMITE = 1_000_000


def update_service():
    """Retorna versão e URL validadas; falhas nunca significam aplicativo atualizado."""
    pedido = Request(
        API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "DLPDownloader",
        },
    )
    try:
        with urlopen(pedido, timeout=5) as resposta:
            if resposta.status != 200:
                raise ValueError("status HTTP")
            dados = resposta.read(LIMITE + 1)
        if len(dados) > LIMITE:
            raise ValueError("resposta excessiva")
        release = json.loads(dados)
        versao = normalizar_versao(release["tag_name"])
        url = release["html_url"]
        destino = urlparse(url)
        if (
            destino.scheme != "https"
            or destino.netloc != "github.com"
            or not destino.path.startswith("/mateusb6315/DLPDownloader/releases/tag/")
            or release.get("draft", True)
            or release.get("prerelease", True)
        ):
            raise ValueError("release inválida")
        return versao, url
    except (URLError, OSError, ValueError, KeyError, TypeError, AttributeError) as erro:
        raise ErroAplicacao(
            "Não foi possível verificar se há atualizações. Tente novamente mais tarde."
        ) from erro
