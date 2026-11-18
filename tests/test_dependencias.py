"""Ferramentas nunca são resolvidas implicitamente pelo PATH."""

import threading

import pytest

from services._infra.dependencias import localizar, verificar
from services._models.erros import ErroDependencia
from tests.apoio_vendor import criar_vendor


def test_ausencia_de_vendor_nao_usa_path(tmp_path):
    with pytest.raises(ErroDependencia):
        localizar(tmp_path)


def test_hash_adulterado_rejeitado(tmp_path, monkeypatch):
    vendor = criar_vendor(tmp_path)
    (vendor / "deno/deno.exe").write_bytes(b"alterado")
    monkeypatch.setattr("services._infra.dependencias.executar", lambda *a, **k: None)
    with pytest.raises(ErroDependencia, match="Integridade"):
        verificar(tmp_path, threading.Event())
