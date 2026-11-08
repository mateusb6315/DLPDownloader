"""Execução cancelável de processos sem shell ou dependência de Qt."""

import os
import queue
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path

from dlpdownloader.modelos.erros import Cancelado, ErroDownload


def encerrar_arvore(processo: subprocess.Popen) -> None:
    """Encerra apenas a árvore do PID iniciado por esta operação."""
    if os.name == "nt":
        ferramenta = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/taskkill.exe"
        subprocess.run(
            [str(ferramenta), "/PID", str(processo.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(processo.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if processo.poll() is None:
        processo.kill()
    processo.wait(timeout=10)


def _ler_saida(saida, fila: queue.Queue, parar: threading.Event) -> None:
    """Lê chunks limitados e preserva fragmentos de linhas sem crescimento ilimitado."""
    pendente = b""
    try:
        while not parar.is_set():
            trecho = saida.read1(8192)
            if not trecho:
                break
            pendente += trecho
            linhas = pendente.split(b"\n")
            pendente = linhas.pop()
            if len(pendente) > 1_048_576:
                raise ErroDownload("A ferramenta emitiu uma linha excessivamente grande.")
            for linha in linhas:
                _enfileirar(fila, linha.decode("utf-8", errors="replace").rstrip("\r"), parar)
        if pendente:
            _enfileirar(fila, pendente.decode("utf-8", errors="replace"), parar)
    except (OSError, ErroDownload) as erro:
        _enfileirar(fila, erro, parar)
    finally:
        _enfileirar(fila, None, parar)


def _enfileirar(fila: queue.Queue, item: object, parar: threading.Event) -> None:
    while not parar.is_set():
        try:
            fila.put(item, timeout=0.1)
            return
        except queue.Full:
            continue


def executar(
    comando: list[str],
    cancelamento: threading.Event,
    ao_receber: Callable[[str], None],
    limite: float = 3600,
) -> None:
    """Executa ferramenta, consumindo saída enquanto observa cancelamento e prazo."""
    if cancelamento.is_set():
        raise Cancelado()
    opcoes = (
        {"creationflags": subprocess.CREATE_NO_WINDOW}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    try:
        processo = subprocess.Popen(
            comando,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            **opcoes,
        )
    except OSError as erro:
        raise ErroDownload("Não foi possível iniciar a ferramenta portátil.") from erro
    arvore = None
    if os.name == "nt":
        from dlpdownloader.servicos.arvore_windows import ArvoreWindows

        try:
            arvore = ArvoreWindows(processo)
        except OSError as erro:
            processo.kill()
            processo.wait(timeout=10)
            processo.stdout.close()
            raise ErroDownload("Não foi possível gerenciar os processos da operação.") from erro
    fila = queue.Queue(maxsize=256)
    parar = threading.Event()
    leitor = threading.Thread(target=_ler_saida, args=(processo.stdout, fila, parar), daemon=True)
    leitor.start()
    inicio = time.monotonic()
    try:
        _consumir(processo, fila, cancelamento, ao_receber, inicio, limite)
    finally:
        parar.set()
        try:
            if processo.poll() is None:
                encerrar_arvore(processo)
        finally:
            if arvore:
                arvore.fechar()
            leitor.join(timeout=5)
            processo.stdout.close()


def _consumir(processo, fila, cancelamento, ao_receber, inicio, limite) -> None:
    while True:
        if cancelamento.is_set():
            encerrar_arvore(processo)
            raise Cancelado()
        if time.monotonic() - inicio > limite:
            encerrar_arvore(processo)
            raise ErroDownload("A ferramenta excedeu o tempo limite de execução.")
        try:
            linha = fila.get(timeout=0.1)
        except queue.Empty:
            continue
        if linha is None:
            break
        if isinstance(linha, Exception):
            raise linha
        ao_receber(linha)
    while processo.poll() is None:
        if cancelamento.wait(0.1):
            encerrar_arvore(processo)
            raise Cancelado()
        if time.monotonic() - inicio > limite:
            raise ErroDownload("A ferramenta excedeu o tempo limite de execução.")
    if cancelamento.is_set():
        raise Cancelado()
    if processo.returncode:
        raise ErroDownload(
            "A ferramenta falhou. Confira o link, a conexão e o espaço livre. "
            "O perfil escolhido pode estar indisponível."
        )
