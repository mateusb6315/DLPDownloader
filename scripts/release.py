"""Gera a pasta portátil, o 7z e o instalador da release com Nuitka."""

import argparse
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._distribuicao_nuitka import gerar_distribuicao
from scripts.comum import RAIZ, status
from scripts.versao_build import solicitar_versao
from services._models.erros import ErroAplicacao


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versao", help="Versão X.Y.Z. Omitir para perguntar")
    parser.add_argument("--destino", type=Path, default=RAIZ / "releases")
    parser.add_argument("--zip", action="store_true", help="Gerar também ZIP da pasta inteira")
    parser.add_argument(
        "--baixar-compilador", action="store_true", help="Usar Zig e permitir seu download"
    )
    args = parser.parse_args(argv)
    try:
        versao = args.versao if args.versao is not None else solicitar_versao()
        gerar_distribuicao(
            versao,
            args.destino,
            beta=False,
            baixar_compilador=args.baixar_compilador,
            criar_zip=args.zip,
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
