"""Ferramentas nunca são resolvidas implicitamente pelo PATH."""

import hashlib
import json
import threading
from pathlib import Path

import pytest

from dlpdownloader.modelos.erros import ErroDependencia
from dlpdownloader.servicos.dependencias import localizar, verificar


def test_ausencia_de_vendor_nao_usa_path(tmp_path):
    with pytest.raises(ErroDependencia):
        localizar(tmp_path)


def test_hash_adulterado_rejeitado(tmp_path, monkeypatch):
    vendor = tmp_path / "vendor"
    arquivos = {}
    for nome in ("yt-dlp/yt-dlp.exe", "ffmpeg/ffmpeg.exe", "ffmpeg/ffprobe.exe", "deno/deno.exe"):
        caminho = vendor / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(b"executavel")
        arquivos[nome] = hashlib.sha256(b"executavel").hexdigest()
    (vendor / "manifest.json").write_text("{}")
    manifesto = hashlib.sha256((vendor / "manifest.json").read_bytes()).hexdigest()
    (vendor / "installed.json").write_text(
        json.dumps({"manifesto_sha256": manifesto, "arquivos": arquivos})
    )
    (vendor / "deno/deno.exe").write_bytes(b"alterado")
    monkeypatch.setattr("dlpdownloader.servicos.dependencias.executar", lambda *a, **k: None)
    with pytest.raises(ErroDependencia, match="Integridade"):
        verificar(tmp_path, threading.Event())


def test_diretorio_frozen_usa_executavel(monkeypatch, tmp_path):
    from dlpdownloader.config.caminhos import raiz_projeto

    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(tmp_path / "App.exe"))
    assert raiz_projeto() == Path(tmp_path)
