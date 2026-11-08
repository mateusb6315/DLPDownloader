"""Integração real com processos Python locais, sem rede ou mídia externa."""

import ctypes
import sys
import threading

import pytest

from dlpdownloader.modelos.erros import Cancelado, ErroDownload
from dlpdownloader.servicos.processos import executar


def test_saida_fragmentada_recomposta_e_sem_deadlock():
    linhas = []
    codigo = (
        "import os; os.write(1,b'prime'); os.write(1,b'ira\\n'); "
        "os.write(2,b'x'*100000+b'\\n'); os.write(1,b'ultima')"
    )
    executar([sys.executable, "-u", "-c", codigo], threading.Event(), linhas.append, limite=10)
    assert linhas[0] == "primeira"
    assert len(linhas[1]) == 100000
    assert linhas[-1] == "ultima"


def test_erro_de_processo_nao_zero():
    with pytest.raises(ErroDownload):
        executar([sys.executable, "-c", "raise SystemExit(2)"], threading.Event(), lambda e: None)


def test_cancelamento_observado_mesmo_sem_saida():
    cancelar = threading.Event()

    def receber(linha):
        if linha == "iniciado":
            cancelar.set()

    codigo = "import time; print('iniciado',flush=True); time.sleep(30)"
    with pytest.raises(Cancelado):
        executar([sys.executable, "-u", "-c", codigo], cancelar, receber, limite=5)


def test_timeout_encerra_processo():
    with pytest.raises(ErroDownload, match="tempo limite"):
        executar(
            [sys.executable, "-c", "import time;time.sleep(30)"],
            threading.Event(),
            lambda e: None,
            limite=0.2,
        )


def test_executavel_ausente():
    with pytest.raises(ErroDownload, match="iniciar"):
        executar(["executavel-que-nao-existe-dlp"], threading.Event(), lambda e: None)


def test_cancelamento_encerra_processo_filho():
    cancelar = threading.Event()
    filhos = []
    codigo = (
        "import subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); "
        "print(p.pid,flush=True);time.sleep(30)"
    )

    def receber(linha):
        filhos.append(int(linha))
        cancelar.set()

    with pytest.raises(Cancelado):
        executar([sys.executable, "-u", "-c", codigo], cancelar, receber, limite=5)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    handle = kernel.OpenProcess(0x1000, False, filhos[0])
    if handle:
        try:
            retorno = ctypes.c_ulong()
            assert kernel.GetExitCodeProcess(handle, ctypes.byref(retorno))
            assert retorno.value != 259  # STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)


def test_job_libera_filho_quando_pai_ja_terminou():
    filhos = []
    codigo = (
        "import subprocess,sys; "
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); "
        "print(p.pid,flush=True)"
    )
    with pytest.raises(ErroDownload, match="tempo limite"):
        executar(
            [sys.executable, "-u", "-c", codigo],
            threading.Event(),
            lambda linha: filhos.append(int(linha)),
            limite=0.5,
        )
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    handle = kernel.OpenProcess(0x1000, False, filhos[0])
    if handle:
        try:
            retorno = ctypes.c_ulong()
            assert kernel.GetExitCodeProcess(handle, ctypes.byref(retorno))
            assert retorno.value != 259
        finally:
            kernel.CloseHandle(handle)
