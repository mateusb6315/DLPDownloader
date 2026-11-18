"""Inicia o reparador e coordena a restauração das ferramentas portáteis."""

import csv
import io
import os
import subprocess
from pathlib import Path

from services._infra.bloqueios import bloquear_uso
from services._infra.preparacao import baixar, preparar


def reparo_disponivel(raiz: Path) -> bool:
    """Consulta se o reparador portátil acompanha o aplicativo."""
    return (raiz / "vendor/repair.exe").is_file()


def iniciar_reparo(raiz: Path) -> None:
    """Abre um console independente e informa ao reparador qual PID aguardar."""
    executavel = raiz / "vendor/repair.exe"
    subprocess.Popen(
        [str(executavel), "--aguardar-pid", str(os.getpid())],
        cwd=executavel.parent,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        close_fds=True,
    )


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


def reparar(raiz: Path, manifesto: Path, *, dados: Path, obter=baixar) -> None:
    """Restaura a partir do manifesto incorporado após impedir o uso concorrente."""
    verificar_fechado()
    with bloquear_uso(dados, exclusivo=True):
        verificar_fechado()
        print("Baixando e verificando as ferramentas necessárias. Aguarde...", flush=True)
        preparar(
            raiz, obter=obter, manifesto_confiavel=manifesto, antes_de_instalar=verificar_fechado
        )
        print("Reparo concluído. Você já pode abrir o DLP Downloader.", flush=True)
