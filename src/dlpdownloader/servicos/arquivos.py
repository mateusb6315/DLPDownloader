"""Escrita atômica de JSON e validação do diretório de saída."""

import json
import os
import tempfile
from pathlib import Path

from dlpdownloader.modelos.erros import ErroDestino


def gravar_json(caminho: Path, dados: object) -> None:
    """Substitui um JSON apenas depois de gravá-lo completamente no mesmo volume."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=caminho.parent, delete=False
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario:
            temporario.unlink(missing_ok=True)


def validar_destino(destino: Path) -> None:
    """Confirma diretório existente e permissão real, sem criar uma pasta inesperada."""
    try:
        if not destino.is_dir():
            raise ErroDestino("A pasta de destino não existe. Escolha outra pasta.")
        with tempfile.TemporaryFile(dir=destino):
            pass
    except OSError as erro:
        raise ErroDestino("Não foi possível gravar na pasta escolhida.") from erro
