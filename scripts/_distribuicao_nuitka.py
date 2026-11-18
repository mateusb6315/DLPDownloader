"""Coordena o staging e a publicação dos artefatos dos canais Nuitka."""

import os
import tempfile
from contextlib import ExitStack
from pathlib import Path

from scripts._artefatos import comando_instalador, executar_etapa, localizar_ferramenta
from scripts._nuitka_build import compilar_nuitka
from scripts.comum import RAIZ, bloqueio, status, validar_nome
from scripts.versao_build import versao_base


class _ErroReversaoPublicacao(RuntimeError):
    """A publicação falhou e ao menos um artefato permanece no destino."""


def _localizar_compactador_e_instalador() -> tuple[Path, Path]:
    programas = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    programas_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    sete_zip = localizar_ferramenta("7z", [programas / "7-Zip/7z.exe"])
    iscc = localizar_ferramenta(
        "ISCC", [programas_x86 / "Inno Setup 7/ISCC.exe", programas / "Inno Setup 7/ISCC.exe"]
    )
    return sete_zip, iscc


def _promover(artefatos: tuple[Path, ...], destino: Path, staging: Path) -> None:
    publicados = []
    try:
        for artefato in artefatos:
            publicados.append((artefato, artefato.rename(destino / artefato.name)))
    except BaseException as erro_publicacao:
        falhas = []
        for origem, final in reversed(publicados):
            try:
                final.rename(origem)
            except (OSError, KeyboardInterrupt) as erro_reversao:
                falhas.append((final, erro_reversao))
        if falhas:
            detalhes = "\n".join(f"- {final}: {erro}" for final, erro in falhas)
            raise _ErroReversaoPublicacao(
                f"Falha ao publicar: {erro_publicacao!s}\n"
                f"Artefatos preservados em {staging}. Revise os itens que ficaram no destino:\n"
                f"{detalhes}"
            ) from BaseExceptionGroup(
                "Falhas de publicação e reversão",
                [erro_publicacao, *(erro for _, erro in falhas)],
            )
        raise


def gerar_distribuicao(
    versao: str,
    destino: Path,
    *,
    beta: bool,
    baixar_compilador: bool = False,
    criar_zip: bool = False,
) -> Path:
    """Compila e valida os artefatos antes de promover o conjunto no destino."""
    if beta:
        validar_nome(versao)
    versao_base(RAIZ, versao, beta)
    if os.name != "nt":
        raise RuntimeError("A distribuição suportada deve ser compilada no Windows.")
    destino = destino.resolve()
    base = f"DLPDownloader-{versao}"
    compactados = (f"{base}.7z", f"{base}.zip") if criar_zip else (f"{base}.7z",)
    nome_instalador = f"{base}-setup.exe"
    with bloqueio(destino / ".compilacao.lock"):
        for nome in (base, *compactados, nome_instalador):
            if (destino / nome).exists():
                raise FileExistsError(f"Já existe um artefato com esse nome: {destino / nome}")
        sete_zip, iscc = _localizar_compactador_e_instalador()
        with ExitStack() as limpeza:
            pasta = tempfile.TemporaryDirectory(prefix=".nuitka-", dir=destino, delete=False)
            staging = Path(pasta.name)
            limpeza.callback(pasta.cleanup)
            pacote = compilar_nuitka(
                staging, versao, beta=beta, baixar_compilador=baixar_compilador
            )
            arquivos = [staging / nome for nome in compactados]
            instalador = staging / nome_instalador
            status("Compactando e verificando o pacote com 7-Zip…")
            for arquivo in arquivos:
                executar_etapa([str(sete_zip), "a", str(arquivo), pacote.name], cwd=staging)
                executar_etapa([str(sete_zip), "t", str(arquivo)], cwd=staging)

            status("Gerando o instalador com Inno Setup…")
            comando, ambiente = comando_instalador(iscc, pacote, staging, versao, beta)
            executar_etapa(comando, env=ambiente)
            (staging / "instalador.exe").rename(instalador)
            for caminho in (*arquivos, instalador):
                if not caminho.is_file() or caminho.stat().st_size == 0:
                    raise RuntimeError(f"A ferramenta não gerou um arquivo válido: {caminho.name}")
            try:
                _promover((pacote, *arquivos, instalador), destino, staging)
            except _ErroReversaoPublicacao:
                limpeza.pop_all()
                raise
    status(f"Pacote, {'7z, ZIP' if criar_zip else '7z'} e instalador disponíveis em {destino}.")
    return destino / base
