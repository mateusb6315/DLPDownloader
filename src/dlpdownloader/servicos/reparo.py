"""Inicia o reparador em uma janela de terminal independente."""

import os
import subprocess
from pathlib import Path


def iniciar_reparo(raiz: Path) -> None:
    """Aguarda o encerramento do processo atual antes de reparar."""
    executavel = raiz / "vendor/repair.exe"
    subprocess.Popen(
        [str(executavel), "--aguardar-pid", str(os.getpid())],
        cwd=executavel.parent,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        close_fds=True,
    )
