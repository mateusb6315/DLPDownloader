"""Empacota a beta completa com Nuitka; produção e beta simples usam PyInstaller."""

import importlib.metadata
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import threading
from pathlib import Path

from dlpdownloader.servicos.dependencias import verificar
from scripts.compilar import ambiente_compilacao
from scripts.compilar_beta import validar_nome
from scripts.comum import RAIZ, bloqueio, status
from scripts.pacote import copiar_vendor
from scripts.validar_pacote import validar_pacote
from scripts.versao_build import preparar_versao, versao_base

# Qt Widgets usa Fusion e PNG nativo; HTTPS e processamento de mídia não passam pelo Qt.
PLUGIN_QT_EXCLUIDOS = (
    "imageformats,iconengines,mediaservice,printsupport,platformthemes,styles,tls,"
    "egldeviceintegrations,xcbglintegrations"
)
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


def montar_comando(
    raiz: Path, pasta: Path, *, repair: bool = False, baixar_compilador: bool = False
) -> list[str]:
    saida = pasta / ("reparador" if repair else "aplicativo")
    comando = [
        sys.executable,
        "-u",
        "-m",
        "nuitka",
        "--update-check=never",
        "--experimental=force-dependencies-pefile",
        "--lto=auto",
        "--noinclude-pytest-mode=nofollow",
        "--noinclude-setuptools-mode=nofollow",
        f"--output-dir={saida}",
        f"--report={saida.parent / (saida.name + '.xml')}",
    ]
    if baixar_compilador:
        comando += ["--zig", "--assume-yes-for-downloads"]
    else:
        comando.append("--msvc=latest")
    if repair:
        vendor = pasta / "pacote/vendor"
        return comando + [
            "--mode=onefile",
            "--windows-console-mode=force",
            "--output-filename=repair.exe",
            f"--include-data-files={vendor / 'manifest.json'}=manifest.json",
            f"--include-data-files={vendor / 'licenses/README.md'}=licenses/README.md",
            str(raiz / "scripts/repair.py"),
        ]
    icone = raiz / "src/dlpdownloader/recursos/flet.png"
    return comando + [
        "--mode=standalone",
        "--windows-console-mode=disable",
        "--output-folder-name=dlp.dist",
        "--output-filename=DLPDownloader.exe",
        "--enable-plugin=pyqt6",
        "--include-module=versao_build",
        "--include-qt-plugins=platforms",
        f"--noinclude-qt-plugins={PLUGIN_QT_EXCLUIDOS}",
        "--noinclude-qt-translations",
        "--python-flag=no_docstrings",
        f"--windows-icon-from-ico={pasta / 'icone.ico'}",
        f"--include-data-files={icone}=dlpdownloader/recursos/flet.png",
        str(raiz / "main.py"),
    ]


def comprimir_executavel(upx: str, executavel: Path) -> None:
    antes = executavel.stat().st_size
    executar_build([upx, "--best", "--lzma", str(executavel)], executavel.parent)
    executar_build([upx, "-t", str(executavel)], executavel.parent)
    depois = executavel.stat().st_size
    status(f"UPX {executavel.name}: {antes:,} → {depois:,} bytes (economia: {antes - depois:,}).")


def comprimir_extensoes_qt(upx: str, pacote: Path) -> None:
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
                executar_build(
                    [upx, "--best", "--lzma", "-o", str(compactada), str(extensao)], pacote
                )
                executar_build([upx, "-t", str(compactada)], pacote)
                depois = compactada.stat().st_size
                if depois < antes:
                    compactada.replace(extensao)
                    status(f"UPX {nome}: {antes:,} → {depois:,} bytes.")
                else:
                    status(f"UPX {nome}: mantida sem compressão por não reduzir o tamanho.")
        except (IndexError, OSError, RuntimeError, pefile.PEFormatError) as erro:
            status(f"UPX {nome}: mantida sem compressão ({erro}).")


def compilar_nuitka(
    destino: Path, versao: str, raiz: Path = RAIZ, *, baixar_compilador: bool = False
) -> Path:
    """Compila e valida os dois EXEs antes de publicar a pasta standalone."""
    if sysconfig.get_platform() != "win-amd64":
        raise RuntimeError("Use Python x64 no Windows para compilar esta distribuição.")
    for nome in ("Nuitka", "PyQt6", "Pillow", "pefile"):
        importlib.metadata.version(nome)
    if not baixar_compilador:
        verificar_msvc()
    upx = shutil.which("upx")
    if upx is None:
        raise FileNotFoundError("UPX não encontrado. Instale-o e inclua-o no PATH.")
    executar_build([upx, "--version"], raiz, limite=15)
    verificar(raiz, threading.Event())
    if not (raiz / "vendor/installed.json").is_file():
        raise RuntimeError("Prepare as ferramentas antes de compilar.")
    final = destino / f"DLPDownloader-{validar_nome(versao)}"
    with bloqueio(destino / ".compilacao.lock"):
        if final.exists():
            raise FileExistsError(f"Já existe um pacote com esse nome: {final}")
        with tempfile.TemporaryDirectory(prefix=".nuitka-", dir=destino) as staging:
            pasta = Path(staging)
            preparar_versao(raiz, pasta, versao, beta=True)
            from PIL import Image

            with Image.open(raiz / "flet.png") as imagem:
                imagem.save(pasta / "icone.ico")
            ambiente = ambiente_compilacao()
            ambiente["PYTHONPATH"] = os.pathsep.join(map(str, (raiz / "src", raiz, pasta)))
            if not baixar_compilador:
                ambiente["CFLAGS"] = f"{ambiente.get('CFLAGS', '')} /O1".strip()
            compilador = "Zig (downloads permitidos)" if baixar_compilador else "MSVC"
            status(f"Compilando o aplicativo com Nuitka e {compilador}…")
            executar_build(
                montar_comando(raiz, pasta, baixar_compilador=baixar_compilador),
                pasta,
                ambiente=ambiente,
            )
            pacote = pasta / "pacote"
            (pasta / "aplicativo/dlp.dist").rename(pacote)
            with bloqueio(raiz / ".preparacao.lock"):
                copiar_vendor(raiz / "vendor", pacote / "vendor")
            status(f"Compilando o reparador com Nuitka e {compilador}…")
            executar_build(
                montar_comando(raiz, pasta, repair=True, baixar_compilador=baixar_compilador),
                pasta,
                ambiente=ambiente,
            )
            reparador = pacote / "vendor/repair.exe"
            (pasta / "reparador/repair.exe").rename(reparador)
            comprimir_executavel(upx, pacote / "DLPDownloader.exe")
            comprimir_executavel(upx, reparador)
            comprimir_extensoes_qt(upx, pacote)
            shutil.copy2(raiz / "README.md", pacote / "README.md")
            status("Validando interface, mídia local e recursos incorporados do reparador…")
            validar_pacote(
                pacote,
                pasta / "dados-smoke",
                plataforma="windows",
                versao_beta=versao_base(raiz, versao, beta=True),
            )
            executar_build(
                [str(reparador), "--verificar-empacotamento"],
                pasta,
                limite=60,
                ocultar_console=True,
            )
            pacote.rename(final)
    status(f"Beta disponível em {final}.")
    return final
