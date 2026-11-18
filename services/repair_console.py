"""Repara as ferramentas da distribuição usando um manifesto incorporado."""

import argparse
import ctypes
import subprocess
import sys
import zipfile
from ctypes import wintypes
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.paths import diretorio_dados
from services._infra.manifesto import ler_manifesto
from services._models.erros import ErroAplicacao
from services.repair import reparar


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


def executar(compilado, entrada: str) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aguardar-pid", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--verificar-empacotamento", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if getattr(compilado, "onefile", False):
        raiz = Path(compilado.containing_dir).resolve().parent
        recursos = Path(entrada).resolve().parent
    elif getattr(sys, "frozen", False):
        raiz = Path(sys.executable).resolve().parent.parent
        recursos = Path(sys._MEIPASS)
    else:
        print("Execute o repair.exe fornecido dentro da pasta vendor.")
        return 1
    manifesto = recursos / "manifest.json"
    try:
        if args.verificar_empacotamento:
            ler_manifesto(recursos)
            if not (recursos / "licenses/README.md").read_text(encoding="utf-8").strip():
                raise ValueError("O aviso de licenças incorporado está vazio.")
            if recursos == raiz / "vendor" or not (raiz / "DLPDownloader.exe").is_file():
                raise ValueError("Não foi possível localizar o pacote externo ao reparador.")
            return 0
        if args.aguardar_pid is not None:
            mostrar_terminal()
            aguardar_processo(args.aguardar_pid)
        reparar(raiz, manifesto, dados=diretorio_dados())
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


def main(compilado=None, *, entrada: str | None = None) -> int:
    """Executa a CLI e mantém a mensagem final visível no console interativo."""
    try:
        return executar(compilado, entrada or __file__)
    finally:
        if "--verificar-empacotamento" not in sys.argv[1:] and sys.stdin and sys.stdin.isatty():
            import msvcrt

            print("\nPressiona qualquer tecla para sair...", end="", flush=True)
            msvcrt.getwch()


if __name__ == "__main__":
    raise SystemExit(main(globals().get("__compiled__")))
