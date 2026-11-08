"""Prepara ambiente reproduzível com Poetry já instalado no Python selecionado."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Mostra o interpretador utilizado e instala as dependências do lock."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    if not (3, 13) <= sys.version_info[:2] < (3, 15):
        print("Use Python 3.13 ou 3.14.", file=sys.stderr)
        return 1
    print(f"Python selecionado: {sys.executable}", flush=True)
    raiz = Path(__file__).resolve().parents[1]
    try:
        subprocess.run([sys.executable, "-m", "poetry", "install"], cwd=raiz, check=True)
    except (OSError, subprocess.CalledProcessError):
        print("Instale Poetry neste Python: python -m pip install poetry", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
