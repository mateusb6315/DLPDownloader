"""Pequenos contratos de CLI, caminhos e escrita de metadados."""

import json
import os
from contextlib import contextmanager
from pathlib import Path

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


@contextmanager
def bloqueio(arquivo: Path):
    """Impede duas compilações simultâneas no mesmo destino."""
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with arquivo.open("a+b") as trava:
        if arquivo.stat().st_size == 0:
            trava.write(b"0")
            trava.flush()
        trava.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(trava.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as erro:
            raise RuntimeError("Outra compilação está em andamento.") from erro
        try:
            yield
        finally:
            trava.seek(0)
            if os.name == "nt":
                msvcrt.locking(trava.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(trava.fileno(), fcntl.LOCK_UN)
