"""Adaptador independente do protocolo estruturado do yt-dlp portátil."""

import json
from dataclasses import replace
from pathlib import Path

from services._infra.dependencias import Ferramentas
from services._infra.processos import executar
from services._models.download import SolicitacaoDownload
from services._models.erros import ErroDownload
from services._models.formatos import argumentos_formato
from services._models.progresso import PREFIXO_RESULTADO, interpretar_progresso

TEMPLATE_PROGRESSO = (
    'download:DLP_PROGRESS:{"etapa":"baixando","faixa":%(info.format_id)j,"progresso":%(progress)j}'
)
TEMPLATE_FINALIZANDO = 'postprocess:DLP_PROGRESS:{"etapa":"finalizando","progresso":{}}'


def montar_comando(
    pedido: SolicitacaoDownload,
    ferramentas: Ferramentas,
    trabalho: Path,
) -> list[str]:
    """Constrói argumentos sem shell, mantendo -P no destino escolhido."""
    # Bitrate explícito exige nosso FFmpeg: ExtractAudio pode copiar o codec existente.
    perfil = replace(pedido, perfil="original", bitrate=None) if pedido.bitrate else pedido
    return [
        str(ferramentas.yt_dlp),
        "--ignore-config",
        "--no-plugin-dirs",
        "--no-playlist",
        "--no-overwrites",
        "--no-post-overwrites",
        "--newline",
        "--progress",
        "--progress-delta",
        "0.1",
        "--encoding",
        "utf-8",
        "--windows-filenames",
        "--socket-timeout",
        "30",
        "--retries",
        "3",
        "--fragment-retries",
        "3",
        "--ffmpeg-location",
        str(ferramentas.ffmpeg.parent),
        "--js-runtimes",
        f"deno:{ferramentas.deno}",
        "--progress-template",
        TEMPLATE_PROGRESSO,
        "--progress-template",
        TEMPLATE_FINALIZANDO,
        "--print",
        "after_move:DLP_RESULT:%(filepath)j",
        "--no-simulate",
        "-P",
        str(pedido.destino),
        "-P",
        f"temp:{trabalho}",
        "-o",
        f"{trabalho.name}/%(title).160B [%(id)s].%(ext)s",
        *argumentos_formato(perfil),
        "--",
        pedido.url,
    ]


def baixar_faixas(
    pedido, ferramentas, trabalho, cancelamento, progresso, executar_processo=executar
) -> Path:
    resultado = []

    def receber(linha: str) -> None:
        evento = interpretar_progresso(linha)
        if evento:
            progresso(evento)
        elif linha.startswith(PREFIXO_RESULTADO):
            try:
                caminho = json.loads(linha[len(PREFIXO_RESULTADO) :])
                if isinstance(caminho, str):
                    resultado.append(Path(caminho).resolve())
            except ValueError:
                raise ErroDownload("Resposta final inválida do yt-dlp.") from None
        # Não registrar saída bruta: ela pode conter URLs assinadas ou credenciais.

    comando = montar_comando(pedido, ferramentas, trabalho)
    executar_processo(comando, cancelamento, receber)
    if len(resultado) != 1:
        raise ErroDownload("O yt-dlp não confirmou um único arquivo final.")
    caminho = resultado[0]
    if not caminho.is_relative_to(trabalho) or not caminho.is_file():
        raise ErroDownload("O arquivo final não foi encontrado na pasta da operação.")
    if caminho.stat().st_size == 0:
        raise ErroDownload("A ferramenta gerou um arquivo vazio.")
    return caminho
