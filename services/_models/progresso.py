"""Eventos estruturados e cálculo de progresso de cada faixa."""

import json
import math
from dataclasses import dataclass

PREFIXO_PROGRESSO = "DLP_PROGRESS:"
PREFIXO_RESULTADO = "DLP_RESULT:"


@dataclass(frozen=True)
class EventoProgresso:
    """Medições de uma faixa; percentual ausente representa total desconhecido."""

    etapa: str
    faixa: str = ""
    baixados: float = 0
    total: float | None = None
    velocidade: float | None = None
    eta: float | None = None
    estimado: bool = False

    @property
    def percentual(self) -> int | None:
        """Retorna percentual limitado, calculado apenas com total positivo."""
        if not self.total:
            return None
        return min(100, max(0, int(100 * self.baixados / self.total)))


def numero(valor: object) -> float | None:
    """Normaliza valores ausentes, inválidos ou não finitos."""
    if isinstance(valor, bool):
        return None
    try:
        resultado = float(valor)
    except (TypeError, ValueError, OverflowError):
        return None
    return resultado if math.isfinite(resultado) and resultado >= 0 else None


def interpretar_progresso(linha: str) -> EventoProgresso | None:
    """Interpreta exclusivamente nosso protocolo JSON, ignorando ruído de terminal."""
    if not linha.startswith(PREFIXO_PROGRESSO):
        return None
    try:
        dados = json.loads(linha[len(PREFIXO_PROGRESSO) :])
        progresso = dados["progresso"]
        total = numero(progresso.get("total_bytes"))
        estimativa = numero(progresso.get("total_bytes_estimate"))
        return EventoProgresso(
            etapa=str(dados.get("etapa", "baixando")),
            faixa=str(dados.get("faixa") or ""),
            baixados=numero(progresso.get("downloaded_bytes")) or 0,
            total=total or estimativa or None,
            velocidade=numero(progresso.get("speed")),
            eta=numero(progresso.get("eta")),
            estimado=not total and bool(estimativa),
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
