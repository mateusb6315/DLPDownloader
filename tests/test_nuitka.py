"""Exercita as entradas públicas das compilações Nuitka."""

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from config import paths
from scripts import _distribuicao_nuitka, release

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


@pytest.mark.parametrize("falha_na_reversao", [False, True])
def test_release_reverte_todos_os_artefatos_possiveis(
    tmp_path, monkeypatch, capsys, falha_na_reversao
):
    base = "DLPDownloader-1.3.2"
    instalador = f"{base}-setup.exe"
    arquivo_retido = tmp_path / f"{base}.zip"

    def compilar(staging, _versao, **_opcoes):
        pacote = staging / base
        pacote.mkdir()
        return pacote

    def executar(comando, *, cwd=None, env=None):
        if comando[1] == "a":
            Path(comando[2]).write_bytes(b"arquivo")
        elif env is not None:
            saida = Path(env["DLP_SAIDA"].replace("{{", "{"))
            (saida / "instalador.exe").write_bytes(b"instalador")

    renomear = Path.rename

    def renomear_com_falha(origem, destino):
        if destino == tmp_path / instalador:
            raise PermissionError("Instalador bloqueado ao publicar.")
        if falha_na_reversao and origem == arquivo_retido:
            raise PermissionError("ZIP bloqueado ao reverter.")
        return renomear(origem, destino)

    monkeypatch.setattr(_distribuicao_nuitka, "compilar_nuitka", compilar)
    monkeypatch.setattr(_distribuicao_nuitka, "localizar_ferramenta", lambda nome, _: Path(nome))
    monkeypatch.setattr(_distribuicao_nuitka, "executar_etapa", executar)
    monkeypatch.setattr(Path, "rename", renomear_com_falha)

    assert release.main(["--destino", str(tmp_path), "--versao", "1.3.2", "--zip"]) == 1
    assert set(tmp_path.glob("DLPDownloader-*")) == (
        {arquivo_retido} if falha_na_reversao else set()
    )
    saida = capsys.readouterr().out
    assert "Instalador bloqueado ao publicar." in saida
    if falha_na_reversao:
        (staging,) = tmp_path.glob(".nuitka-*")
        assert str(staging) in saida
        assert str(arquivo_retido) in saida
        assert "ZIP bloqueado ao reverter." in saida
        assert (staging / base).is_dir()
        assert (staging / f"{base}.7z").read_bytes() == b"arquivo"
        assert (staging / instalador).read_bytes() == b"instalador"
        assert arquivo_retido.read_bytes() == b"arquivo"
    else:
        assert not list(tmp_path.glob(".nuitka-*"))


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
