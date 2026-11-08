"""Compilação beta isolada da publicação de produção."""

import pytest

from scripts.compilar_beta import compilar_beta, validar_nome
from tests.apoio_vendor import criar_vendor
from tests.test_compilar import compilador_falso


@pytest.mark.parametrize("nome", ["1.3.0_beta1", "teste livre", "1.4-rc+teste", "qualquer"])
def test_nomes_livres(nome):
    assert validar_nome(nome) == nome


@pytest.mark.parametrize("nome", ["", "../fora", "a/b", "a\\b", "a:b", "fim.", " nome"])
def test_nome_inseguro_recusado(nome):
    with pytest.raises(ValueError):
        validar_nome(nome)


def test_beta_isolado_sem_relatorio(tmp_path, monkeypatch):
    criar_vendor(tmp_path)
    (tmp_path / "README.md").write_text("Documentação", encoding="utf-8")
    monkeypatch.setattr("scripts.compilar_beta.validar_pacote", lambda *a: None)
    destino = compilar_beta(
        tmp_path,
        executar=compilador_falso,
        validar_ferramentas=lambda *a: None,
        versao="1.3.0_beta1",
        criar_zip=True,
    )
    assert destino == tmp_path / "releases/beta/DLPDownloader-1.3.0_beta1"
    assert (destino / "DLPDownloader.exe").exists()
    assert (destino / "vendor/repair.exe").exists()
    assert destino.with_name(destino.name + ".zip").exists()
    assert not list(destino.parent.glob("*.json"))
    with pytest.raises(RuntimeError, match="existe"):
        compilar_beta(
            tmp_path,
            executar=compilador_falso,
            validar_ferramentas=lambda *a: None,
            versao="1.3.0_beta1",
        )
