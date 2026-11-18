"""Confere as entradas públicas da aplicação pelo protocolo de diagnóstico."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("entrada", [("-m", "dlpdownloader"), ("main.py",)])
def test_diagnostico_sem_pasta_termina_antes_de_iniciar_qt(entrada):
    resultado = subprocess.run(
        [sys.executable, *entrada, "--verificar-midia"],
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "QT_QPA_PLATFORM": "invalido"},
        cwd=RAIZ,
        timeout=15,
        check=False,
    )

    assert resultado.returncode == 2, resultado.stderr
    assert "Uso: --verificar-midia <dados>" in resultado.stderr
