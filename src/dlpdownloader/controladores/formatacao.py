"""Apresenta medidas do progresso ao controlador sem alterar os valores recebidos."""

from dlpdownloader.config.interface import TEXTOS


def formatar_bytes(valor: float | None) -> str:
    """Converte bytes para uma unidade legível."""
    if valor is None:
        return TEXTOS["desconhecido"]
    for unidade in ("B", "KiB", "MiB", "GiB", "TiB"):
        if valor < 1024 or unidade == "TiB":
            return TEXTOS["bytes"].format(valor=valor, unidade=unidade)
        valor /= 1024
    return TEXTOS["desconhecido"]


def formatar_detalhes(evento) -> str:
    """Mantém ausências explícitas e sinaliza tamanho estimado."""
    velocidade = TEXTOS["desconhecido"]
    if evento.velocidade is not None:
        velocidade = TEXTOS["velocidade"].format(valor=formatar_bytes(evento.velocidade))
    eta = TEXTOS["desconhecido"] if evento.eta is None else TEXTOS["eta"].format(valor=evento.eta)
    total = formatar_bytes(evento.total)
    if evento.estimado:
        total += TEXTOS["estimado"]
    return TEXTOS["transferencia"].format(
        baixados=formatar_bytes(evento.baixados),
        total=total,
        velocidade=velocidade,
        eta=eta,
    )
