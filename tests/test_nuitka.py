"""Exercita as entradas públicas das compilações da arquitetura raiz."""

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from config import paths

RAIZ = Path(__file__).resolve().parents[1]


def test_seletor_delega_a_beta_e_retorna_falha_de_nome_invalido(tmp_path):
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "scripts/nuitka.py"), "--versao", "beta?"],
        input="1\n",
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        cwd=tmp_path,
        timeout=15,
        check=False,
    )

    assert resultado.returncode == 1, resultado.stderr
    assert "1 — Beta" in resultado.stdout
    assert "2 — Release" in resultado.stdout
    assert "caracteres não permitidos" in resultado.stdout


def test_autoteste_sem_pasta_falha_sem_iniciar_qt():
    resultado = subprocess.run(
        [sys.executable, "-m", "config.bootstrap", "--verificar-midia"],
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "QT_QPA_PLATFORM": "invalido"},
        cwd=RAIZ,
        timeout=15,
        check=False,
    )

    assert resultado.returncode == 2, resultado.stderr
    assert "--verificar-midia <dados>" in resultado.stderr


def test_distribuicao_procura_vendor_ao_lado_do_executavel(tmp_path, monkeypatch):
    pacote = tmp_path / "DLPDownloader-beta"
    monkeypatch.setattr(sys, "executable", str(pacote / "DLPDownloader.exe"))
    monkeypatch.setattr(
        paths,
        "__compiled__",
        SimpleNamespace(standalone=True, containing_dir=str(tmp_path)),
        raising=False,
    )

    assert paths.raiz_projeto() == pacote
