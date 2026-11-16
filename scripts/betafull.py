"""Compila pacote beta, arquivo 7z e instalador para testes locais."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.distribuicao_full import main as distribuir
from scripts.nuitka_beta import compilar_nuitka


def main() -> int:
    return distribuir(
        beta=True, compilador=compilar_nuitka, versao_padrao="1.3.2-beta2", downloads_nuitka=True
    )


if __name__ == "__main__":
    raise SystemExit(main())
