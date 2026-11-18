"""Erros apresentados pelo controlador sem expor detalhes técnicos."""


class ErroAplicacao(Exception):
    """Falha conhecida e compreensível pelo usuário."""


class ErroDependencia(ErroAplicacao):
    """Ferramenta portátil ausente ou inválida."""


class ErroDownload(ErroAplicacao):
    """Download, conversão ou validação final falhou."""


class ErroDestino(ErroAplicacao):
    """Destino indisponível ou sem permissão."""


class Cancelado(ErroAplicacao):
    """Cancelamento solicitado pelo usuário."""


class SubstituicaoRecusada(Cancelado):
    """O usuário optou por manter o arquivo existente."""
