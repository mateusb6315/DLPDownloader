"""Extração restrita de arquivos esperados e verificação de SHA-256."""

import hashlib
import zipfile

import pytest

from scripts.preparar_ferramentas import extrair


def test_zip_nao_extrai_caminhos_arbitrarios(tmp_path):
    arquivo = tmp_path / "pacote.zip"
    with zipfile.ZipFile(arquivo, "w") as pacote:
        pacote.writestr("bin/ffmpeg.exe", b"exe")
        pacote.writestr("../../nao-extrair.txt", b"x")
    ferramenta = {
        "nome": "ffmpeg",
        "sha256": hashlib.sha256(arquivo.read_bytes()).hexdigest(),
        "arquivos": {"ffmpeg.exe": "ffmpeg/ffmpeg.exe"},
    }
    staging = tmp_path / "staging"
    staging.mkdir()
    extrair(arquivo, ferramenta, staging)
    assert (staging / "ffmpeg/ffmpeg.exe").read_bytes() == b"exe"
    assert len(list(staging.rglob("*.*"))) == 1


def test_checksum_errado_nao_instala(tmp_path):
    arquivo = tmp_path / "programa.exe"
    arquivo.write_bytes(b"alterado")
    ferramenta = {"nome": "exemplo", "sha256": "0" * 64, "arquivos": {"a": "a.exe"}}
    with pytest.raises(ValueError, match="SHA-256"):
        extrair(arquivo, ferramenta, tmp_path / "staging")
    assert not (tmp_path / "staging").exists()
