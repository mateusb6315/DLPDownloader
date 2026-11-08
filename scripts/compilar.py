"""Compila uma distribuição Windows onedir sem depender de arquivo .spec."""

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
from scripts.comum import RAIZ, bloqueio, status
from scripts.validar_pacote import validar_pacote


def montar_comando(raiz: Path, temporario: Path) -> list[str]:
    """Todos os parâmetros de empacotamento são definidos aqui."""
    return [
        sys.executable,
        "-u",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--noupx",
        "--name",
        "DLPDownloader",
        "--paths",
        str(raiz / "src"),
        "--distpath",
        str(temporario / "dist"),
        "--workpath",
        str(temporario / "work"),
        "--specpath",
        str(temporario),
        "--icon",
        str(raiz / "flet.png"),
        "--add-data",
        f"{raiz / 'src/dlpdownloader/recursos'}:dlpdownloader/recursos",
        str(raiz / "main.py"),
    ]


def executar_compilador(comando: list[str], executar=subprocess.run) -> None:
    """Oculta saída no sucesso e mostra até 30 linhas de diagnóstico na falha."""
    try:
        executar(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            env=ambiente_compilacao(),
        )
    except subprocess.CalledProcessError as erro:
        status("Últimas linhas do PyInstaller:")
        print("\n".join(((erro.stdout or "") + (erro.stderr or "")).splitlines()[-30:]))
        raise


def ambiente_compilacao() -> dict[str, str]:
    """Evita coletar DLLs incompatíveis de Git, Poppler ou outro software no PATH."""
    import PyQt6

    ambiente = dict(os.environ)
    windows = Path(ambiente.get("SystemRoot", r"C:\Windows"))
    caminhos = [
        Path(PyQt6.__file__).parent / "Qt6/bin",
        Path(sys.executable).parent,
        Path(sys.base_prefix),
        windows / "System32",
        windows,
    ]
    ambiente["PATH"] = os.pathsep.join(map(str, caminhos))
    for nome in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH", "PYTHONHOME"):
        ambiente.pop(nome, None)
    return ambiente


def solicitar_versao() -> str:
    """Solicita uma versão com três componentes numéricos."""
    mensagem = "Digite a próxima versão: "
    while True:
        versao = input(mensagem).strip()
        if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", versao):
            return versao
        mensagem = "Formato inválido. Tente novamente: "


def compilar(
    raiz: Path = RAIZ,
    destino: Path | None = None,
    executar=subprocess.run,
    validar_ferramentas=None,
) -> Path:
    """Compila e publica a versão informada pelo usuário."""
    from dlpdownloader.servicos.dependencias import verificar

    destino = destino or raiz / "releases"
    status("Verificando pré-requisitos…")
    if os.name != "nt":
        raise RuntimeError("A distribuição suportada deve ser compilada no Windows.")
    for nome in ("PyInstaller", "Pillow", "PyQt6"):
        importlib.metadata.version(nome)
    (validar_ferramentas or verificar)(raiz, threading.Event())
    if not (raiz / "vendor/installed.json").is_file():
        raise RuntimeError("Prepare as ferramentas antes de compilar.")
    versao = solicitar_versao()
    with bloqueio(destino / ".compilacao.lock"):
        final = destino / f"DLPDownloader-{versao}"
        with tempfile.TemporaryDirectory(prefix=".compilacao-", dir=destino) as pasta:
            temporario = Path(pasta)
            status("Fazendo a compilação…")
            executar_compilador(montar_comando(raiz, temporario), executar)
            pacote = temporario / "dist/DLPDownloader"
            if not (pacote / "DLPDownloader.exe").is_file():
                raise RuntimeError("O compilador não gerou o executável esperado.")
            shutil.copytree(
                raiz / "vendor", pacote / "vendor", ignore=shutil.ignore_patterns(".cache", "*.zip")
            )
            shutil.copy2(raiz / "README.md", pacote / "README.md")
            status("Validando inicialização do pacote sem ferramentas globais…")
            validar_pacote(pacote, temporario / "dados-smoke")
            status(f"Publicando {final.name}…")
            pacote.rename(final)
    status("Compilação concluída.")
    return final


def main() -> int:
    """CLI com retornos 0, 1 ou 130; o .spec temporário não é uma entrada."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, help="Pasta de releases (padrão: releases/)")
    args = parser.parse_args()
    try:
        compilar(destino=args.destino.resolve() if args.destino else None)
    except KeyboardInterrupt:
        status("Compilação interrompida pelo usuário.")
        return 130
    except (
        OSError,
        EOFError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
        importlib.metadata.PackageNotFoundError,
        ErroAplicacao,
    ) as erro:
        status(f"ERRO: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
