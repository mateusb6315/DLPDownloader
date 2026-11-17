"""Localiza MSVC e executa Nuitka e UPX."""

import os
import subprocess
import tempfile
from pathlib import Path

from scripts.comum import status

EXTENSOES_QT_UPX = ("QtCore.pyd", "QtGui.pyd", "QtWidgets.pyd", "sip.pyd")


def verificar_msvc() -> None:
    """Detecta instalações registradas com ferramentas C++ para x86/x64."""
    programas = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    vswhere = programas / "Microsoft Visual Studio/Installer/vswhere.exe"
    if vswhere.is_file():
        resultado = subprocess.run(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-prerelease",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        if resultado.stdout.strip():
            return
    raise RuntimeError(
        "MSVC x64 não encontrado. No Visual Studio Installer, instale a carga de trabalho "
        "Desenvolvimento para desktop com C++ e um SDK do Windows, ou use --baixar-compilador."
    )


def executar_build(
    comando: list[str], pasta: Path, *, ambiente=None, limite=None, ocultar_console=False
) -> None:
    try:
        subprocess.run(
            comando,
            cwd=pasta,
            env=ambiente,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=limite,
            creationflags=subprocess.CREATE_NO_WINDOW if ocultar_console else 0,
        )
    except subprocess.CalledProcessError as erro:
        linhas = "\n".join(((erro.stdout or "") + "\n" + (erro.stderr or "")).splitlines()[-30:])
        raise RuntimeError(f"Falha ao executar {Path(comando[0]).name}:\n{linhas}") from erro


def comprimir_executavel(upx: str, executavel: Path) -> None:
    antes = executavel.stat().st_size
    executar_build([upx, "--best", "--lzma", str(executavel)], executavel.parent)
    executar_build([upx, "-t", str(executavel)], executavel.parent)
    depois = executavel.stat().st_size
    status(f"UPX {executavel.name}: de {antes:,} para {depois:,} bytes.")


def comprimir_extensoes_qt(upx: str, pacote: Path, *, executar=executar_build) -> None:
    """Comprime só extensões conhecidas sem assinatura e guarda o original em caso de falha."""
    import pefile

    for nome in EXTENSOES_QT_UPX:
        extensao = pacote / "PyQt6" / nome
        if not extensao.is_file():
            continue
        try:
            with pefile.PE(str(extensao), fast_load=True) as pe:
                seguranca = pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]
                if pe.OPTIONAL_HEADER.DATA_DIRECTORY[seguranca].Size:
                    status(f"UPX {nome}: assinatura preservada.")
                    continue
            antes = extensao.stat().st_size
            with tempfile.TemporaryDirectory(prefix=".upx-", dir=pacote.parent) as pasta:
                compactada = Path(pasta) / nome
                executar([upx, "--best", "--lzma", "-o", str(compactada), str(extensao)], pacote)
                executar([upx, "-t", str(compactada)], pacote)
                depois = compactada.stat().st_size
                if depois < antes:
                    compactada.replace(extensao)
                    status(f"UPX {nome}: de {antes:,} para {depois:,} bytes.")
                else:
                    status(f"UPX {nome}: mantida sem compressão por não reduzir o tamanho.")
        except (IndexError, OSError, RuntimeError, pefile.PEFormatError) as erro:
            status(f"UPX {nome}: mantida sem compressão ({erro}).")
