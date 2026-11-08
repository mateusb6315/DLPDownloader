"""Compila pacote local para desenvolvimento, sem publicar no GitHub."""

import argparse
import importlib.metadata
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dlpdownloader.modelos.erros import ErroAplicacao
from scripts.compilar import executar_compilador, montar_comando
from scripts.compilar_repair import compilar_repair
from scripts.comum import RAIZ, bloqueio, status
from scripts.pacote import copiar_vendor
from scripts.validar_pacote import validar_pacote
from scripts.versao_build import preparar_versao


def validar_nome(nome: str) -> str:
    """Aceita nomes livres que possam ser usados como parte de arquivo Windows."""
    if not nome or nome != nome.strip() or nome.endswith("."):
        raise ValueError("Informe um nome não vazio, sem espaços nas extremidades ou ponto final.")
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', nome):
        raise ValueError("O nome contém caracteres não permitidos no Windows.")
    return nome


def compilar_beta(
    raiz: Path = RAIZ,
    destino: Path | None = None,
    executar=subprocess.run,
    validar_ferramentas=None,
    versao: str | None = None,
    criar_zip: bool = False,
) -> Path:
    """Gera uma pasta local independente, sem relatório ou histórico de versões."""
    from dlpdownloader.servicos.dependencias import verificar

    status("Verificando pré-requisitos…")
    if os.name != "nt":
        raise RuntimeError("A distribuição suportada deve ser compilada no Windows.")
    for nome in ("PyInstaller", "Pillow", "PyQt6"):
        importlib.metadata.version(nome)
    (validar_ferramentas or verificar)(raiz, threading.Event())
    if not (raiz / "vendor/installed.json").is_file():
        raise RuntimeError("Prepare as ferramentas antes de compilar.")
    versao = validar_nome(versao if versao is not None else input("Nome do beta: ").strip())
    destino = destino or raiz / "releases" / "beta"
    destino.mkdir(parents=True, exist_ok=True)
    final = destino / f"DLPDownloader-{versao}"
    zip_final = destino / f"{final.name}.zip"
    if final.exists() or zip_final.exists():
        raise RuntimeError("Já existe um pacote com esse nome no destino.")
    with tempfile.TemporaryDirectory(prefix=".beta-", dir=destino) as pasta:
        temporario = Path(pasta)
        preparar_versao(raiz, temporario, versao, beta=True)
        status("Fazendo a compilação beta…")
        executar_compilador(montar_comando(raiz, temporario), executar)
        pacote = temporario / "dist/DLPDownloader"
        if not (pacote / "DLPDownloader.exe").is_file():
            raise RuntimeError("O compilador não gerou o executável esperado.")
        with bloqueio(raiz / ".preparacao.lock"):
            copiar_vendor(raiz / "vendor", pacote / "vendor")
            compilar_repair(raiz, temporario, pacote / "vendor", executar_compilador, executar)
        shutil.copy2(raiz / "README.md", pacote / "README.md")
        validar_pacote(pacote, temporario / "dados-smoke")
        zip_publicado = False
        try:
            if criar_zip:
                arquivo_zip = Path(
                    shutil.make_archive(
                        str(temporario / "pacote"),
                        "zip",
                        root_dir=pacote.parent,
                        base_dir=pacote.name,
                    )
                )
                with arquivo_zip.open("rb") as origem, zip_final.open("xb") as saida:
                    zip_publicado = True
                    shutil.copyfileobj(origem, saida)
            pacote.rename(final)
        except BaseException:
            if zip_publicado:
                zip_final.unlink(missing_ok=True)
            raise
    status(f"Beta disponível em {final}.")
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--versao", help="Nome livre; convenção: 1.3.0_beta1")
    parser.add_argument("--destino", type=Path, help="Pasta de saída (padrão: releases/beta/)")
    parser.add_argument("--zip", action="store_true", help="Criar também um ZIP local")
    args = parser.parse_args()
    try:
        compilar_beta(
            destino=args.destino.resolve() if args.destino else None,
            versao=args.versao,
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
        importlib.metadata.PackageNotFoundError,
        ErroAplicacao,
    ) as erro:
        status(f"ERRO: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
