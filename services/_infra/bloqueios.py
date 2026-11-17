"""Bloqueios de uso da aplicação e de operações nos diretórios gerenciados."""

import ctypes
import os
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
    import msvcrt

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


@contextmanager
def bloqueio(arquivo: Path):
    """Impede duas compilações simultâneas no mesmo destino."""
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with arquivo.open("a+b") as trava:
        if arquivo.stat().st_size == 0:
            trava.write(b"0")
            trava.flush()
        trava.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(trava.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(trava.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as erro:
            raise RuntimeError("Outra compilação está em andamento.") from erro
        try:
            yield
        finally:
            trava.seek(0)
            if os.name == "nt":
                msvcrt.locking(trava.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(trava.fileno(), fcntl.LOCK_UN)
