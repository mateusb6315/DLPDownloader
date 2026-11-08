"""Git simulado: nenhuma operação altera refs ou conversa com o remoto."""

import subprocess

import pytest

from scripts.git_workflow import GitWorkflow, criar_parser


def criar_fluxo(tmp_path, falhar=None, stage=""):
    chamadas = []

    def executar(comando, **kwargs):
        chamadas.append(comando)
        assert kwargs["cwd"] == tmp_path and kwargs["check"]
        if falhar and falhar in comando:
            raise subprocess.CalledProcessError(1, comando)
        saida = ""
        if "--show-toplevel" in comando:
            saida = str(tmp_path)
        elif "--cached" in comando:
            saida = stage
        elif "--show-current" in comando:
            saida = "codex/exemplo"
        elif comando == ["git", "remote"]:
            saida = "servidor"
        return subprocess.CompletedProcess(comando, 0, stdout=saida)

    return GitWorkflow(tmp_path, executar), chamadas


def test_commit_adiciona_somente_arquivos_indicados(tmp_path):
    fluxo, chamadas = criar_fluxo(tmp_path)
    args = criar_parser().parse_args(["commit", "-m", "Mudança", "--arquivos", "main.py"])
    fluxo.executar_acao(args)
    assert ["git", "--literal-pathspecs", "add", "--", "main.py"] in chamadas
    assert not any("push" in comando for comando in chamadas)


def test_commit_recusa_stage_preexistente(tmp_path):
    fluxo, chamadas = criar_fluxo(tmp_path, stage="outro.py")
    args = criar_parser().parse_args(["commit", "-m", "Mudança", "--arquivos", "main.py"])
    with pytest.raises(ValueError, match="stage"):
        fluxo.executar_acao(args)
    assert not any("add" in comando for comando in chamadas)


@pytest.mark.parametrize("nome", ["..", "../fora.py", ":(glob)*"])
def test_commit_recusa_escopo_amplo(tmp_path, nome):
    fluxo, chamadas = criar_fluxo(tmp_path)
    args = criar_parser().parse_args(["commit", "-m", "Mudança", "--arquivos", nome])
    with pytest.raises(ValueError):
        fluxo.executar_acao(args)
    assert not any("add" in comando for comando in chamadas)


def test_merge_com_conflito_interrompe_sem_push(tmp_path):
    fluxo, chamadas = criar_fluxo(tmp_path, falhar="merge")
    with pytest.raises(subprocess.CalledProcessError):
        fluxo.executar_acao(criar_parser().parse_args(["merge-local", "--origem", "feature"]))
    assert chamadas[-1] == ["git", "merge", "--no-edit", "feature"]
    assert not any("push" in comando for comando in chamadas)


def test_publicar_usa_branch_atual_e_remoto_configurado(tmp_path):
    fluxo, chamadas = criar_fluxo(tmp_path)
    fluxo.executar_acao(criar_parser().parse_args(["publicar"]))
    assert chamadas[-1] == [
        "git",
        "push",
        "-u",
        "servidor",
        "codex/exemplo:refs/heads/codex/exemplo",
    ]
