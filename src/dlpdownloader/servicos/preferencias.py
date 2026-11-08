"""Persistência da pasta escolhida sem escrever ao lado do executável."""

import json
from pathlib import Path

from dlpdownloader.servicos.arquivos import gravar_json


class Preferencias:
    """Repositório de preferências com caminho injetável para testes."""

    def __init__(self, arquivo: Path, padrao: Path):
        self.arquivo = arquivo
        self.padrao = padrao

    def carregar(self) -> tuple[Path, str]:
        """Lê a pasta e devolve aviso recuperável sem apagar arquivo inválido."""
        if not self.arquivo.exists():
            return self.padrao, ""
        try:
            dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
            if dados["versao"] != 1 or not isinstance(dados["diretorio"], str):
                raise ValueError("Esquema inválido")
            destino = Path(dados["diretorio"])
            if not destino.is_absolute() or not destino.is_dir():
                return destino, "A pasta salva está indisponível. Escolha outra pasta."
            return destino, ""
        except (OSError, ValueError, KeyError, TypeError):
            return self.padrao, "Preferências inválidas; escolha a pasta novamente para salvar."

    def salvar(self, diretorio: Path) -> None:
        """Persiste imediatamente uma escolha aceita pelo controlador."""
        gravar_json(self.arquivo, {"versao": 1, "diretorio": str(diretorio)})
