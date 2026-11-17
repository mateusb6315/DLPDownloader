"""Empacota a beta completa com Nuitka; produção e beta simples usam PyInstaller."""

import importlib.metadata
import os
import shutil
import sys
import sysconfig
import tempfile
import threading
from pathlib import Path

from dlpdownloader.servicos.dependencias import verificar
from scripts._nuitka_tools import (
    comprimir_executavel,
    executar_build,
    verificar_msvc,
)
from scripts._nuitka_tools import comprimir_extensoes_qt as _comprimir_extensoes_qt
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


def comprimir_extensoes_qt(upx: str, pacote: Path) -> None:
    _comprimir_extensoes_qt(upx, pacote, executar=executar_build)


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
