"""Gera a pasta portátil, o 7z e o instalador beta com Nuitka."""

import argparse
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._distribuicao_nuitka import gerar_distribuicao
from scripts.comum import RAIZ, status, validar_nome
from services._models.erros import ErroAplicacao


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versao", help="Nome válido para arquivo no Windows")
    parser.add_argument("--destino", type=Path, default=RAIZ / "releases/beta")
    parser.add_argument(
        "--baixar-compilador", action="store_true", help="Usar Zig e permitir seu download"
    )
    args = parser.parse_args(argv)
    try:
        versao = validar_nome(
            args.versao if args.versao is not None else input("Nome da beta: ").strip()
        )
        gerar_distribuicao(
            versao, args.destino, beta=True, baixar_compilador=args.baixar_compilador
        )
    except KeyboardInterrupt:
        status("Compilação interrompida pelo usuário.")
        return 130
    except (
        OSError,
        EOFError,
        ValueError,
        RuntimeError,
        subprocess.SubprocessError,
        ErroAplicacao,
    ) as erro:
        status(f"ERRO: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
