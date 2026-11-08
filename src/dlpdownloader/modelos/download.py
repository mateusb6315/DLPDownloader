"""Solicitações e estados do único download ativo."""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from urllib.parse import urlsplit

from dlpdownloader.config.perfis import PERFIS
from dlpdownloader.modelos.erros import ErroAplicacao


class Estado(Enum):
    """Estados da aplicação e de seu trabalho em segundo plano."""

    VERIFICANDO = auto()
    INDISPONIVEL = auto()
    PRONTO = auto()
    PREPARANDO = auto()
    BAIXANDO = auto()
    FINALIZANDO = auto()
    CANCELANDO = auto()
    CONCLUIDO = auto()
    FALHOU = auto()
    CANCELADO = auto()


ATIVOS = frozenset({Estado.PREPARANDO, Estado.BAIXANDO, Estado.FINALIZANDO, Estado.CANCELANDO})
TRANSICOES = {
    Estado.VERIFICANDO: {Estado.VERIFICANDO, Estado.PRONTO, Estado.INDISPONIVEL, Estado.CANCELANDO},
    Estado.INDISPONIVEL: {Estado.VERIFICANDO},
    Estado.PRONTO: {Estado.PREPARANDO},
    Estado.PREPARANDO: {
        Estado.BAIXANDO,
        Estado.FINALIZANDO,
        Estado.CANCELANDO,
        Estado.CONCLUIDO,
        Estado.FALHOU,
        Estado.CANCELADO,
    },
    Estado.BAIXANDO: {
        Estado.BAIXANDO,
        Estado.FINALIZANDO,
        Estado.CANCELANDO,
        Estado.CONCLUIDO,
        Estado.FALHOU,
        Estado.CANCELADO,
    },
    Estado.FINALIZANDO: {
        Estado.FINALIZANDO,
        Estado.BAIXANDO,
        Estado.CANCELANDO,
        Estado.CONCLUIDO,
        Estado.FALHOU,
        Estado.CANCELADO,
    },
    Estado.CANCELANDO: {Estado.CANCELANDO, Estado.CANCELADO, Estado.CONCLUIDO, Estado.FALHOU},
    Estado.CONCLUIDO: {Estado.PRONTO},
    Estado.FALHOU: {Estado.PRONTO},
    Estado.CANCELADO: {Estado.PRONTO},
}


def validar_transicao(atual: Estado, proximo: Estado) -> None:
    """Rejeita uma mudança fora do ciclo de vida documentado."""
    if proximo not in TRANSICOES[atual]:
        raise ValueError(f"Transição inválida: {atual.name} -> {proximo.name}")


@dataclass(frozen=True)
class SolicitacaoDownload:
    """Opções imutáveis de uma operação; validar antes de executar."""

    url: str
    perfil: str
    bitrate: int | None
    destino: Path

    def validar(self) -> None:
        """Rejeita URL ou combinação inválida, sem realizar I/O."""
        try:
            partes = urlsplit(self.url)
            valido = partes.scheme in {"http", "https"} and partes.hostname
            valido = valido and not partes.username and not partes.password
            valido = valido and not any(c.isspace() or ord(c) < 32 for c in self.url)
            _ = partes.port
        except ValueError:
            valido = False
        if not valido:
            raise ErroAplicacao("Informe um link HTTP ou HTTPS válido, sem credenciais.")
        perfil = next((p for p in PERFIS if p[0] == self.perfil), None)
        if perfil is None:
            raise ErroAplicacao("Escolha um formato disponível.")
        permitidos = perfil[3] or (None,)
        if self.bitrate not in permitidos:
            raise ErroAplicacao("O bitrate escolhido não é válido para este formato.")
        if not self.destino.is_absolute():
            raise ErroAplicacao("Escolha um diretório de destino absoluto.")
