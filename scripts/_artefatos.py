"""Executa as ferramentas de arquivamento e instalação."""

import os
import shutil
import subprocess
from pathlib import Path

from scripts.comum import RAIZ


def localizar_ferramenta(nome: str, candidatos: list[Path]) -> Path:
    encontrado = shutil.which(nome)
    for caminho in ([Path(encontrado)] if encontrado else []) + candidatos:
        if caminho.is_file():
            return caminho.resolve()
    raise FileNotFoundError(f"Ferramenta {nome} não encontrada. Instale-a ou inclua-a no PATH.")


def executar_etapa(comando: list[str], **kwargs) -> None:
    try:
        subprocess.run(
            comando,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            **kwargs,
        )
    except subprocess.CalledProcessError as erro:
        diagnostico = "\n".join(((erro.stdout or "") + (erro.stderr or "")).splitlines()[-30:])
        raise RuntimeError(f"Falha em {Path(comando[0]).name}:\n{diagnostico}") from erro


def comando_instalador(
    iscc: Path, pacote: Path, saida: Path, versao: str, beta: bool
) -> tuple[list[str], dict[str, str]]:
    """Aciona o modelo Inno comum e escapa chaves em valores para Inno Setup."""
    ambiente = os.environ.copy()
    ambiente.update(
        DLP_PACOTE=str(pacote).replace("{", "{{"),
        DLP_VERSAO=versao.replace("{", "{{"),
        DLP_SAIDA=str(saida).replace("{", "{{"),
        DLP_BETA="1" if beta else "0",
    )
    return [str(iscc), str(RAIZ / "scripts/instalador.iss")], ambiente
