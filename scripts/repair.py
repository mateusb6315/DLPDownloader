"""Repara as ferramentas da distribuição usando um manifesto incorporado."""

import argparse
import csv
import ctypes
import io
import os
import subprocess
import sys
import zipfile
from ctypes import wintypes
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dlpdownloader.config.caminhos import diretorio_dados
from dlpdownloader.modelos.erros import ErroAplicacao
from dlpdownloader.servicos.uso import bloquear_uso
from scripts.preparar_ferramentas import preparar


def verificar_fechado() -> None:
    """Detecta inclusive versões anteriores que ainda não usam bloqueio compartilhado."""
    ferramenta = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/tasklist.exe"
    try:
        resultado = subprocess.run(
            [str(ferramenta), "/FI", "IMAGENAME eq DLPDownloader.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            check=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as erro:
        raise RuntimeError("Não foi possível verificar se o DLP Downloader está fechado.") from erro
    if any(
        linha and linha[0].casefold() == "dlpdownloader.exe"
        for linha in csv.reader(io.StringIO(resultado.stdout))
    ):
        raise RuntimeError("Feche o DLP Downloader antes de prosseguir.")


def reparar(raiz: Path, manifesto: Path) -> None:
    """Reconstrói o conjunto inteiro e preserva o anterior em falhas recuperáveis."""
    verificar_fechado()
    with bloquear_uso(diretorio_dados(), exclusivo=True):
        verificar_fechado()
        print("Baixando e verificando as ferramentas necessárias. Aguarde...", flush=True)
        preparar(raiz, manifesto_confiavel=manifesto, antes_de_instalar=verificar_fechado)
        print("Reparo concluído. Você já pode abrir o DLP Downloader.", flush=True)


def aguardar_processo(pid: int) -> None:
    """Espera a saída completa do downloader antes de verificar processos e bloqueios."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    processo = kernel.OpenProcess(0x00100000, False, pid)
    if not processo:
        if ctypes.get_last_error() == 87:
            return
        raise RuntimeError("Não foi possível aguardar o fechamento do DLP Downloader.")
    try:
        if kernel.WaitForSingleObject(processo, 60000) != 0:
            raise RuntimeError("O DLP Downloader não encerrou. Feche-o e tente novamente.")
    finally:
        kernel.CloseHandle(processo)


def mostrar_terminal() -> None:
    """Solicita ao Windows que mostre e coloque o console recém-aberto à frente."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    usuario = ctypes.WinDLL("user32", use_last_error=True)
    kernel.GetConsoleWindow.restype = wintypes.HWND
    usuario.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    usuario.SetForegroundWindow.argtypes = [wintypes.HWND]
    janela = kernel.GetConsoleWindow()
    if janela:
        usuario.ShowWindow(janela, 5)
        usuario.SetForegroundWindow(janela)


def executar() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aguardar-pid", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not getattr(sys, "frozen", False):
        print("Execute o repair.exe fornecido dentro da pasta vendor.")
        return 1
    raiz = Path(sys.executable).resolve().parent.parent
    manifesto = Path(sys._MEIPASS) / "manifest.json"
    try:
        if args.aguardar_pid is not None:
            mostrar_terminal()
            aguardar_processo(args.aguardar_pid)
        reparar(raiz, manifesto)
    except KeyboardInterrupt:
        print("Reparo cancelado.")
        return 130
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
        ErroAplicacao,
    ) as erro:
        print(f"Não foi possível concluir o reparo: {erro}")
        return 1
    return 0


def main() -> int:
    try:
        return executar()
    finally:
        if sys.stdin and sys.stdin.isatty():
            import msvcrt

            print("\nPressiona qualquer tecla para sair...", end="", flush=True)
            msvcrt.getwch()


if __name__ == "__main__":
    raise SystemExit(main())
