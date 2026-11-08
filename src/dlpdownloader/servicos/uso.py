"""Coordena aplicativo e reparador por bloqueios compartilhados no Windows."""

import ctypes
import msvcrt
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path


class Overlapped(ctypes.Structure):
    _fields_ = [
        ("Internal", ctypes.c_size_t),
        ("InternalHigh", ctypes.c_size_t),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE),
    ]


@contextmanager
def bloquear_uso(dados: Path, exclusivo: bool):
    """Impede reparo com app aberto e abertura de app durante o reparo."""
    dados.mkdir(parents=True, exist_ok=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LockFileEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(Overlapped),
    ]
    kernel.LockFileEx.restype = wintypes.BOOL
    kernel.UnlockFileEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(Overlapped),
    ]
    kernel.UnlockFileEx.restype = wintypes.BOOL
    with (dados / "uso.lock").open("a+b") as arquivo:
        handle = msvcrt.get_osfhandle(arquivo.fileno())
        estado = Overlapped()
        if not kernel.LockFileEx(
            handle, 1 | (2 if exclusivo else 0), 0, 1, 0, ctypes.byref(estado)
        ):
            erro = ctypes.get_last_error()
            if erro in (32, 33, 158):
                raise RuntimeError("Feche o DLP Downloader antes de prosseguir.")
            raise ctypes.WinError(erro)
        try:
            yield
        finally:
            kernel.UnlockFileEx(handle, 0, 1, 0, ctypes.byref(estado))
