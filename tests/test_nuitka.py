"""Exercita as entradas públicas das compilações Nuitka."""

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

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


@pytest.mark.parametrize(
    ("script", "entrada"),
    [("release.py", ""), ("nuitka.py", "2\n")],
)
def test_release_rejeita_versao_beta_pelos_pontos_de_entrada(script, entrada, tmp_path):
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / script), "--versao", "1.3.2-beta1"],
        input=entrada,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        cwd=tmp_path,
        timeout=15,
        check=False,
    )

    assert resultado.returncode == 1, resultado.stderr
    assert "X.Y.Z" in resultado.stdout


def test_release_preserva_zip_existente_e_nao_publica_novos_artefatos(tmp_path):
    destino = tmp_path / "pacotes de release"
    destino.mkdir()
    arquivo_zip = destino / "DLPDownloader-1.3.2.zip"
    arquivo_zip.write_bytes(b"pacote publicado")
    resultado = subprocess.run(
        [
            sys.executable,
            str(RAIZ / "scripts" / "release.py"),
            "--destino",
            str(destino),
            "--versao",
            "1.3.2",
            "--zip",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        cwd=tmp_path,
        timeout=15,
        check=False,
    )

    assert resultado.returncode == 1, resultado.stderr
    assert "Já existe" in resultado.stdout
    assert arquivo_zip.name in resultado.stdout
    assert arquivo_zip.read_bytes() == b"pacote publicado"
    assert list(destino.glob("DLPDownloader-*")) == [arquivo_zip]


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
