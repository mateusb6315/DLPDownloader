"""Textos e valores visuais compartilhados pelas views."""

TITULO = "DLP Downloader"
LARGURA = 660
ALTURA = 420
TEXTOS = {
    "subtitulo": "Seu vídeo ou áudio, no formato que você escolher.",
    "link": "Link do vídeo",
    "placeholder": "Cole um link HTTP ou HTTPS",
    "formato": "Formato de saída",
    "bitrate": "Bitrate de áudio",
    "destino": "Salvar em",
    "escolher": "Escolher pasta",
    "baixar": "Baixar",
    "verificando": "Verificando ferramentas portáteis…",
    "pronto": "Pronto para baixar.",
    "cancelar": "Cancelar",
    "cancelando": "Cancelando e liberando os arquivos…",
    "progresso": "Preparando download…",
    "fechar": "Há um trabalho em andamento. Deseja cancelar e fechar?",
    "sim": "Sim",
    "nao": "Não",
    "dl_concluido": "Download concluído.",
    "confirmar_substituicao": "O arquivo já existe. Deseja substituí-lo?",
    "substituicao_recusada": "O arquivo existente foi mantido.",
    "sucesso": "Arquivo salvo em:\n{caminho}",
    "cancelado": "Operação cancelada.",
    "original": "Original (sem conversão)",
    "kbps": "{valor} kb/s",
    "transferencia": "{baixados} / {total} · {velocidade} · ETA {eta}",
    "bytes": "{valor:.1f} {unidade}",
    "velocidade": "{valor}/s",
    "eta": "{valor:.0f} s",
    "desconhecido": "—",
    "estimado": " (estimado)",
    "percentual": "%p%",
    "indeterminado": "Aguardando dados…",
    "indisponivel": "Ferramentas indisponíveis. Execute scripts/preparar_ferramentas.py.",
}
ETAPAS = {
    "preparando": "Preparando download…",
    "baixando": "Baixando faixa {faixa}",
    "finalizando": "Finalizando download…",
}
CORES = {"fundo": "#f5f7fb", "texto": "#172438", "destaque": "#245dcc"}
ESTILO = """
QWidget { font-size: 14px; }
QLineEdit, QComboBox { padding: 8px; border: 1px solid #bcc7d8; border-radius: 5px; }
QPushButton { padding: 9px 16px; border-radius: 5px; background: #e3e9f3; }
QPushButton#principal { background: #245dcc; color: white; font-weight: bold; }
QPushButton:disabled { background: #dde2eb; color: #788496; }
QLabel#subtitulo { color: #53647b; }
QLabel#status { color: #53647b; }
QProgressBar { border: 1px solid #bcc7d8; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #245dcc; }
"""
