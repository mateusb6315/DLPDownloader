"""Coordena pacote validado, arquivo 7z e instalador Windows."""

import argparse
import importlib.metadata
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from dlpdownloader.modelos.erros import ErroAplicacao
from scripts.compilar import compilar, solicitar_versao
from scripts.compilar_beta import compilar_beta, validar_nome
from scripts.comum import RAIZ, status


def localizar_ferramenta(nome: str, candidatos: list[Path]) -> Path:
    encontrado = shutil.which(nome)
    for caminho in ([Path(encontrado)] if encontrado else []) + candidatos:
        if caminho.is_file():
            return caminho.resolve()
    raise FileNotFoundError(f"Ferramenta {nome} não encontrada. Instale-a ou inclua-a no PATH.")


def executar_etapa(comando: list[str], **kwargs) -> None:
    try:
        subprocess.run(
            comando,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            **kwargs,
        )
    except subprocess.CalledProcessError as erro:
        diagnostico = "\n".join(((erro.stdout or "") + (erro.stderr or "")).splitlines()[-30:])
        raise RuntimeError(f"Falha em {Path(comando[0]).name}:\n{diagnostico}") from erro


def publicar(arquivo: Path, destino: Path) -> None:
    """Publica arquivo completo sem substituir outro, inclusive em corrida."""
    if not arquivo.is_file() or arquivo.stat().st_size == 0:
        raise RuntimeError(f"A ferramenta não gerou um arquivo válido: {arquivo.name}")
    arquivo.rename(destino)


def gerar_full(beta: bool, versao: str | None, destino: Path | None) -> Path:
    if os.name != "nt":
        raise RuntimeError("A distribuição suportada deve ser compilada no Windows.")
    programas = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    programas_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    sete_zip = localizar_ferramenta("7z", [programas / "7-Zip/7z.exe"])
    iscc = localizar_ferramenta(
        "ISCC", [programas_x86 / "Inno Setup 7/ISCC.exe", programas / "Inno Setup 7/ISCC.exe"]
    )
    nome = (
        validar_nome(versao if versao is not None else input("Nome do beta: ").strip())
        if beta
        else (versao if versao is not None else solicitar_versao())
    )
    if not beta and not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", nome):
        raise ValueError("Formato de versão inválido.")
    destino = destino or RAIZ / "releases" / ("beta" if beta else "")
    destino = destino.resolve()
    base = f"DLPDownloader-{nome}"
    arquivo_7z = destino / f"{base}.7z"
    instalador = destino / f"{base}-setup.exe"
    if arquivo_7z.exists() or instalador.exists():
        raise FileExistsError("Já existe um arquivo 7z ou instalador com esse nome no destino.")
    pacote = (compilar_beta if beta else compilar)(destino=destino, versao=nome)
    with tempfile.TemporaryDirectory(prefix=".full-", dir=destino) as pasta:
        temporario = Path(pasta)
        arquivo = temporario / f"{base}.7z"
        status("Compactando o pacote com 7-Zip…")
        executar_etapa([str(sete_zip), "a", "-t7z", str(arquivo), pacote.name], cwd=pacote.parent)
        publicar(arquivo, arquivo_7z)
        status(f"Arquivo criado em: {arquivo_7z}")
        status("Verificando pré-requisitos para gerar o instalador…")
        ambiente = os.environ.copy()
        ambiente.update(
            DLP_PACOTE=str(pacote).replace("{", "{{"),
            DLP_VERSAO=nome.replace("{", "{{"),
            DLP_SAIDA=str(temporario).replace("{", "{{"),
            DLP_BETA="1" if beta else "0",
        )
        status("Iniciando o processo…")
        executar_etapa([str(iscc), str(RAIZ / "scripts/instalador.iss")], env=ambiente)
        publicar(temporario / "instalador.exe", instalador)
        status("Compilação concluída.")
        status(f"Instalador criado em: {instalador}")
    return pacote


def main(beta: bool) -> int:
    parser = argparse.ArgumentParser(description="Compila pacote, arquivo 7z e instalador.")
    parser.add_argument("--versao", help="Nome beta ou versão numérica de produção")
    parser.add_argument("--destino", type=Path, help="Pasta de saída")
    args = parser.parse_args()
    try:
        gerar_full(beta, args.versao, args.destino)
    except KeyboardInterrupt:
        status("Compilação interrompida pelo usuário.")
        return 130
    except (
        OSError,
        EOFError,
        ValueError,
        RuntimeError,
        subprocess.SubprocessError,
        importlib.metadata.PackageNotFoundError,
        ErroAplicacao,
    ) as erro:
        status(f"ERRO: {erro}")
        return 1
    return 0
