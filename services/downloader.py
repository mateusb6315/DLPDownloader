"""Fachada de mídia: validação, staging e publicação segura no destino."""

import os
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from services._infra.arquivos import validar_destino
from services._infra.dependencias import Ferramentas
from services._infra.processos import executar
from services._models.download import SolicitacaoDownload
from services._models.erros import Cancelado, ErroAplicacao, ErroDestino, SubstituicaoRecusada
from services._models.progresso import EventoProgresso
from services.yt_dlp import baixar_faixas


def publicar(origem, destino, cancelamento, confirmar_substituicao) -> Path:
    """Publica atomicamente; colisão exige resposta antes de substituir."""
    if cancelamento.is_set():
        raise Cancelado()
    try:
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
            raise ErroDestino("Não foi possível substituir o arquivo existente.") from falha
    except OSError as erro:
        raise ErroDestino(
            "Não foi possível publicar o arquivo. Verifique permissões e espaço livre."
        ) from erro
    return destino


class ServicoDownload:
    """Executa uma operação isolada sem expor arquivos incompletos."""

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
        """Valida e publica somente após a confirmação do adaptador."""
        pedido.validar()
        if pedido.perfil not in {"mp4", "mkv"}:
            raise ErroAplicacao("Este fluxo de mídia aceita vídeo MP4 ou MKV.")
        validar_destino(pedido.destino)
        try:
            with tempfile.TemporaryDirectory(prefix=".dlp-", dir=pedido.destino) as pasta:
                origem = baixar_faixas(
                    pedido,
                    self.ferramentas,
                    Path(pasta).resolve(),
                    cancelamento,
                    progresso,
                    self.executar_processo,
                )
                return publicar(
                    origem, pedido.destino / origem.name, cancelamento, confirmar_substituicao
                )
        except OSError as erro:
            raise ErroDestino("Falha ao gravar ou liberar arquivos na pasta de destino.") from erro
