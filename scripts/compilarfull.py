"""Compila pacote de produção, arquivo 7z e instalador."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.distribuicao_full import main

if __name__ == "__main__":
    raise SystemExit(main(beta=False))
