"""Comandos e protocolo estruturado do yt-dlp portátil."""

import json
import logging
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from dlpdownloader.modelos.download import SolicitacaoDownload
from dlpdownloader.modelos.erros import Cancelado, ErroDestino, ErroDownload, SubstituicaoRecusada
from dlpdownloader.modelos.formatos import argumentos_formato
from dlpdownloader.modelos.progresso import (
    PREFIXO_RESULTADO,
    EventoProgresso,
    interpretar_progresso,
)
from dlpdownloader.servicos.arquivos import validar_destino
from dlpdownloader.servicos.dependencias import Ferramentas
from dlpdownloader.servicos.processos import executar

LOGGER = logging.getLogger(__name__)
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


class ServicoDownload:
    """Executa uma solicitação isolada em staging e só publica arquivo completo."""

    def __init__(self, ferramentas: Ferramentas, executar_processo=executar):
        self.ferramentas = ferramentas
        self.executar_processo = executar_processo

    def baixar(
        self,
        pedido: SolicitacaoDownload,
        cancelamento: threading.Event,
        progresso: Callable[[EventoProgresso], None],
        confirmar_substituicao: Callable[[], bool] = lambda: False,
    ) -> Path:
        """Baixa/converte e publica sem substituir arquivo existente."""
        pedido.validar()
        validar_destino(pedido.destino)
        try:
            with tempfile.TemporaryDirectory(prefix=".dlp-", dir=pedido.destino) as pasta:
                trabalho = Path(pasta).resolve()
                origem = self._baixar_faixas(pedido, trabalho, cancelamento, progresso)
                if pedido.bitrate:
                    origem = self._converter(pedido, origem, cancelamento, progresso)
                if cancelamento.is_set():
                    raise Cancelado()
                destino = pedido.destino / origem.name
                try:
                    # No Windows rename é atômico e recusa sobrescrita (também em exFAT).
                    if os.name == "nt":
                        origem.rename(destino)
                    else:
                        os.link(origem, destino)
                except FileExistsError as erro:
                    if not confirmar_substituicao():
                        raise SubstituicaoRecusada() from erro
                    if cancelamento.is_set():
                        raise Cancelado()
                    try:
                        os.replace(origem, destino)
                    except OSError as falha:
                        raise ErroDestino(
                            "Não foi possível substituir o arquivo existente."
                        ) from falha
                except OSError as erro:
                    raise ErroDestino(
                        "Não foi possível publicar o arquivo. Verifique permissões e espaço livre."
                    ) from erro
                return destino
        except OSError as erro:
            raise ErroDestino("Falha ao gravar ou liberar arquivos na pasta de destino.") from erro

    def _baixar_faixas(self, pedido, trabalho, cancelamento, progresso) -> Path:
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

        comando = montar_comando(pedido, self.ferramentas, trabalho)
        self.executar_processo(comando, cancelamento, receber)
        if len(resultado) != 1:
            raise ErroDownload("O yt-dlp não confirmou um único arquivo final.")
        caminho = resultado[0]
        if not caminho.is_relative_to(trabalho) or not caminho.is_file():
            raise ErroDownload("O arquivo final não foi encontrado na pasta da operação.")
        if caminho.stat().st_size == 0:
            raise ErroDownload("A ferramenta gerou um arquivo vazio.")
        return caminho

    def _converter(self, pedido, origem, cancelamento, progresso) -> Path:
        progresso(EventoProgresso("finalizando"))
        destino = origem.with_name(f"{origem.stem} - {pedido.bitrate}k.{pedido.perfil}")
        codecs = {"mp3": "libmp3lame", "m4a": "aac", "opus": "libopus"}
        comando = [
            str(self.ferramentas.ffmpeg),
            "-hide_banner",
            "-nostdin",
            "-n",
            "-i",
            str(origem),
            "-vn",
            "-c:a",
            codecs[pedido.perfil],
            "-b:a",
            f"{pedido.bitrate}k",
            str(destino),
        ]
        self.executar_processo(comando, cancelamento, lambda linha: None)
        if not destino.is_file() or not destino.stat().st_size:
            raise ErroDownload("O FFmpeg não confirmou o áudio convertido.")
        return destino
