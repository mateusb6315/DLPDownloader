"""Compila a aplicação em standalone e o reparador em onefile."""

import importlib.metadata
import os
import shutil
import sys
import sysconfig
import threading
from pathlib import Path

from scripts._nuitka_tools import (
    comprimir_executavel,
    comprimir_extensoes_qt,
    executar_build,
    verificar_msvc,
)
from scripts.comum import RAIZ, ambiente_compilacao, bloqueio, status
from scripts.pacote import copiar_vendor
from scripts.validar_pacote import validar_pacote
from scripts.versao_build import preparar_versao, versao_base
from services._infra.dependencias import verificar
from services._models.atualizacoes import VersaoDistribuicao

PLUGIN_QT_EXCLUIDOS = (
    "imageformats,iconengines,mediaservice,printsupport,platformthemes,styles,tls,"
    "egldeviceintegrations,xcbglintegrations"
)


def _comando(saida: Path, baixar_compilador: bool) -> list[str]:
    comando = [
        sys.executable,
        "-u",
        "-P",
        "-m",
        "nuitka",
        "--update-check=never",
        "--experimental=force-dependencies-pefile",
        "--lto=auto",
        "--noinclude-pytest-mode=nofollow",
        "--noinclude-setuptools-mode=nofollow",
        f"--output-dir={saida}",
        f"--report={saida.with_suffix('.xml')}",
    ]
    if baixar_compilador:
        return comando + ["--zig", "--assume-yes-for-downloads"]
    return comando + ["--msvc=latest"]


def _compilar_aplicativo(staging, ambiente, baixar_compilador) -> Path:
    from PIL import Image

    icone = staging / "flet.png"
    shutil.copy2(RAIZ / "ui/resources/flet.png", icone)
    ico = staging / "icone.ico"
    with Image.open(icone) as imagem:
        imagem.save(ico)
    saida = staging / "aplicativo"
    comando = _comando(saida, baixar_compilador) + [
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
        f"--windows-icon-from-ico={ico}",
        f"--include-data-files={icone.name}=ui/resources/flet.png",
        str(RAIZ / "main.py"),
    ]
    executar_build(comando, staging, ambiente=ambiente)
    return saida / "dlp.dist"


def _compilar_reparador(staging, vendor, ambiente, baixar_compilador) -> Path:
    saida = staging / "reparador"
    recursos = vendor.relative_to(staging)
    comando = _comando(saida, baixar_compilador) + [
        "--mode=onefile",
        "--windows-console-mode=force",
        "--output-filename=repair.exe",
        f"--include-data-files={recursos / 'manifest.json'}=manifest.json",
        f"--include-data-files={recursos / 'licenses/README.md'}=licenses/README.md",
        str(RAIZ / "services/repair_console.py"),
    ]
    executar_build(comando, staging, ambiente=ambiente)
    return (saida / "repair.exe").rename(vendor / "repair.exe")


def compilar_nuitka(
    staging: Path, versao: str, *, beta: bool, baixar_compilador: bool = False
) -> Path:
    """Entrega uma pasta validada no staging para empacotamento do canal."""
    if sysconfig.get_platform() != "win-amd64":
        raise RuntimeError("Use Python x64 no Windows para compilar esta distribuição.")
    try:
        for nome in ("Nuitka", "PyQt6", "Pillow", "pefile"):
            importlib.metadata.version(nome)
    except importlib.metadata.PackageNotFoundError as erro:
        raise RuntimeError(
            f"Instale as dependências de desenvolvimento. Falta {erro.name}."
        ) from erro
    if not baixar_compilador:
        verificar_msvc()
    upx = shutil.which("upx") if beta else None
    if beta:
        if upx is None:
            raise FileNotFoundError("UPX não encontrado. Instale-o e inclua-o no PATH.")
        upx = str(Path(upx).resolve())
        executar_build([upx, "--version"], staging, limite=15)

    preparar_versao(RAIZ, staging, versao, beta)
    ambiente = ambiente_compilacao()
    ambiente["PYTHONPATH"] = os.pathsep.join(map(str, (staging, RAIZ)))
    if not baixar_compilador:
        ambiente["CFLAGS"] = f"{ambiente.get('CFLAGS', '')} /O1".strip()
    vendor_provisorio = staging / "vendor"
    with bloqueio(RAIZ / ".preparacao.lock"):
        verificar(RAIZ, threading.Event())
        copiar_vendor(RAIZ / "vendor", vendor_provisorio)

    compilador = "Zig" if baixar_compilador else "MSVC"
    status(f"Compilando o aplicativo com Nuitka e {compilador}…")
    dist = _compilar_aplicativo(staging, ambiente, baixar_compilador)
    pacote = dist.rename(staging / "pacote")
    vendor = vendor_provisorio.rename(pacote / "vendor")

    status(f"Compilando o reparador com Nuitka e {compilador}…")
    reparador = _compilar_reparador(staging, vendor, ambiente, baixar_compilador)
    if upx:
        comprimir_executavel(upx, pacote / "DLPDownloader.exe")
        comprimir_executavel(upx, reparador)
        comprimir_extensoes_qt(upx, pacote)
    shutil.copy2(RAIZ / "README.md", pacote / "README.md")

    status("Validando inicialização, mídia local e recursos do reparador…")
    validar_pacote(
        pacote,
        staging / "dados-smoke",
        plataforma="windows",
        versao=VersaoDistribuicao(versao_base(RAIZ, versao, beta), beta),
    )
    executar_build(
        [str(reparador), "--verificar-empacotamento"], staging, limite=60, ocultar_console=True
    )
    return pacote.rename(staging / f"DLPDownloader-{versao}")
