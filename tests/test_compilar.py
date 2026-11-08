"""Pipeline de publicação com compilador falso e diretórios temporários."""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.compilar import ambiente_compilacao, compilar, executar_compilador, montar_comando
from scripts.comum import bloqueio, ler_historico


@pytest.fixture
def projeto(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.compilar.validar_pacote", lambda *args: None)
    raiz = tmp_path / "projeto"
    (raiz / "vendor").mkdir(parents=True)
    (raiz / "vendor/installed.json").write_text("{}")
    (raiz / "vendor/manifest.json").write_text("{}")
    (raiz / "pyproject.toml").write_text('[project]\nversion="1.0.0"')
    (raiz / "README.md").write_text("Documentação")
    return raiz


def compilador_falso(comando, **kwargs):
    destino = Path(comando[comando.index("--distpath") + 1]) / "DLPDownloader"
    destino.mkdir(parents=True)
    (destino / "DLPDownloader.exe").write_bytes(b"exe")
    assert kwargs["capture_output"] and kwargs["check"]
    return subprocess.CompletedProcess(comando, 0, stdout="saida oculta", stderr="")


def construir(projeto, executor=compilador_falso):
    return compilar(projeto, executar=executor, validar_ferramentas=lambda *a: None)


def test_build_sem_spec_entrada_com_recursos_e_sem_upx(tmp_path):
    comando = montar_comando(tmp_path, tmp_path / "staging")
    assert comando[-1] == str(tmp_path / "main.py")
    assert "--noupx" in comando and "--strip" not in comando
    assert not any(arg.endswith(".spec") for arg in comando)
    assert "--windowed" in comando and "--add-data" in comando


def test_duas_compilacoes_versionadas_e_sem_saida_ruidosa(projeto, capsys):
    primeira = construir(projeto)
    segunda = construir(projeto)
    assert primeira.name.endswith("build.1")
    assert segunda.name.endswith("build.2")
    assert (segunda / "vendor/manifest.json").is_file()
    assert "saida oculta" not in capsys.readouterr().out


@pytest.mark.parametrize("conteudo", ["", "  \n\t", None])
def test_historico_vazio_ou_ausente(projeto, conteudo):
    if conteudo is not None:
        (projeto / "releases").mkdir()
        (projeto / "releases/historico.json").write_text(conteudo)
    assert construir(projeto).name.endswith("build.1")


def test_versao_apagada_nao_reutilizada_e_incremento_inteiro(projeto):
    destino = projeto / "releases"
    destino.mkdir()
    (destino / "historico.json").write_text('[{"numero":9}]')
    assert construir(projeto).name.endswith("build.10")


@pytest.mark.parametrize(
    "conteudo", ["{", "{}", '[{"numero":1},{"numero":1}]', '[{"numero":-1}]', '[{"numero":true}]']
)
def test_historico_invalido_preservado(projeto, conteudo):
    pasta = projeto / "releases"
    pasta.mkdir()
    arquivo = pasta / "historico.json"
    arquivo.write_text(conteudo)
    with pytest.raises(ValueError):
        construir(projeto)
    assert arquivo.read_text() == conteudo


def test_falha_nao_publica_nem_consome_numero(projeto, capsys):
    def falhar(*args, **kwargs):
        raise subprocess.CalledProcessError(2, "pyinstaller", output="diagnostico")

    with pytest.raises(subprocess.CalledProcessError):
        construir(projeto, falhar)
    assert "diagnostico" in capsys.readouterr().out
    assert not (projeto / "releases/historico.json").exists()
    assert construir(projeto).name.endswith("build.1")


def test_executavel_ausente_mesmo_com_retorno_zero(projeto):
    with pytest.raises(RuntimeError, match="executável"):
        construir(projeto, lambda *a, **k: None)
    assert not (projeto / "releases/historico.json").exists()


def test_publicacao_interrompida_reconciliada(projeto):
    primeira = construir(projeto)
    arquivo = projeto / "releases/historico.json"
    arquivo.unlink()
    segunda = construir(projeto)
    assert segunda.name.endswith("build.2") and primeira.is_dir()
    assert len(ler_historico(arquivo)) == 2


def test_bloqueio_concorrente(tmp_path):
    arquivo = tmp_path / ".lock"
    with bloqueio(arquivo):
        with pytest.raises(RuntimeError, match="andamento"):
            with bloqueio(arquivo):
                pass
    with bloqueio(arquivo):
        pass


def test_diagnostico_limitado_a_trinta_linhas(capsys):
    def falhar(*a, **k):
        raise subprocess.CalledProcessError(1, "cmd", output="\n".join(map(str, range(50))))

    with pytest.raises(subprocess.CalledProcessError):
        executar_compilador([], falhar)
    linhas = capsys.readouterr().out.splitlines()
    assert linhas[-1] == "49" and "0" not in linhas


def test_metadados_incluem_versao_python_e_fuso(projeto):
    dados = json.loads((construir(projeto) / "build.json").read_text())
    assert dados["versao"] == "1.0.0"
    assert dados["python"] and dados["data"].endswith("+00:00")


def test_path_do_compilador_nao_herda_dlls_de_outros_programas(monkeypatch):
    monkeypatch.setenv("PATH", r"C:\FerramentaExterna\bin")
    ambiente = ambiente_compilacao()
    assert "FerramentaExterna" not in ambiente["PATH"]
    assert "System32" in ambiente["PATH"]


def test_smoke_test_falho_nao_publica_pacote(projeto, monkeypatch):
    def falhar(*args):
        raise RuntimeError("Falha na inicialização")

    monkeypatch.setattr("scripts.compilar.validar_pacote", falhar)
    with pytest.raises(RuntimeError, match="inicialização"):
        construir(projeto)
    assert not list((projeto / "releases").glob("DLPDownloader-*"))
    assert not (projeto / "releases/historico.json").exists()
