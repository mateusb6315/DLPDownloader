"""Ferramentas nunca são resolvidas implicitamente pelo PATH."""

import threading
from pathlib import Path

import pytest

from dlpdownloader.modelos.erros import ErroDependencia
from dlpdownloader.servicos.dependencias import localizar, verificar
from tests.apoio_vendor import criar_vendor


def test_ausencia_de_vendor_nao_usa_path(tmp_path):
    with pytest.raises(ErroDependencia):
        localizar(tmp_path)


def test_hash_adulterado_rejeitado(tmp_path, monkeypatch):
    vendor = criar_vendor(tmp_path)
    (vendor / "deno/deno.exe").write_bytes(b"alterado")
    monkeypatch.setattr("dlpdownloader.servicos.dependencias.executar", lambda *a, **k: None)
    with pytest.raises(ErroDependencia, match="Integridade"):
        verificar(tmp_path, threading.Event())


def test_diretorio_frozen_usa_executavel(monkeypatch, tmp_path):
    from dlpdownloader.config.caminhos import raiz_projeto

    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(tmp_path / "App.exe"))
    assert raiz_projeto() == Path(tmp_path)
