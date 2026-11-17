"""Obtém versões fixadas das ferramentas portáteis e verifica SHA-256."""

import argparse
import sys
import zipfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.comum import RAIZ
from services._infra.preparacao import baixar as baixar
from services._infra.preparacao import extrair as extrair
from services._infra.preparacao import preparar as preparar_conjunto
from services._models.erros import ErroAplicacao


def preparar(
    raiz: Path = RAIZ,
    obter=baixar,
    manifesto_confiavel: Path | None = None,
    antes_de_instalar=None,
) -> None:
    """Preserva a entrada de preparação usada pelos scripts de distribuição."""
    preparar_conjunto(raiz, obter, manifesto_confiavel, antes_de_instalar)


def main() -> int:
    """CLI de preparação explícita; nenhuma atualização ocorre ao abrir a GUI."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        preparar()
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, ErroAplicacao) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
