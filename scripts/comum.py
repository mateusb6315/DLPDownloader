"""Pequenos contratos de CLI, caminhos e escrita de metadados."""

import json
from pathlib import Path

from services._infra.bloqueios import bloqueio as bloqueio

RAIZ = Path(__file__).resolve().parents[1]


def status(mensagem: str) -> None:
    """Emite uma etapa de compilação com flush imediato."""
    print(f"[compilação] {mensagem}", flush=True)


def ler_historico(arquivo: Path) -> list[dict]:
    """Aceita histórico vazio, mas recusa corrupção sem sobrescrever o original."""
    if not arquivo.exists() or not arquivo.read_text(encoding="utf-8").strip():
        return []
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    if not isinstance(dados, list):
        raise ValueError("Histórico inválido: esperada lista.")
    numeros = []
    for item in dados:
        if not isinstance(item, dict) or type(item.get("numero")) is not int:
            raise ValueError("Histórico contém publicação inválida.")
        numeros.append(item["numero"])
    if any(n < 1 for n in numeros) or len(numeros) != len(set(numeros)):
        raise ValueError("Histórico contém números repetidos ou inválidos.")
    return dados
