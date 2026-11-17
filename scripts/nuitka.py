"""Selecione o canal da distribuição Windows com Nuitka."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import beta


def main(argv: list[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    print("1 — Beta\n2 — Release")
    if argumentos in (["--help"], ["-h"]):
        print("Selecione um canal ou execute beta.py diretamente para ver seus argumentos.")
        return 0
    try:
        escolha = input("Canal: ").strip()
    except KeyboardInterrupt:
        return 130
    except EOFError:
        escolha = ""
    if escolha == "1":
        return beta.main(argumentos)
    if escolha == "2":
        print("O canal Release estará disponível na próxima etapa da migração.")
    else:
        print("Escolha 1 ou 2.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
