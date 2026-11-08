"""Executa lint, formatação e testes rápidos sem downloads reais."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Interrompe no primeiro erro, preservando seu código de saída."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    ambiente = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    raiz = Path(__file__).resolve().parents[1]
    comandos = [
        ["ruff", "check", "src", "scripts", "tests", "main.py"],
        ["ruff", "format", "--check", "src", "scripts", "tests", "main.py"],
        ["pytest", "-q", "-m", "not externo"],
    ]
    for comando in comandos:
        resultado = subprocess.run([sys.executable, "-m", *comando], cwd=raiz, env=ambiente)
        if resultado.returncode:
            return resultado.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
