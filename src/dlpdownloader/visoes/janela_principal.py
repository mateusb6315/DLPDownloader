"""Composição da janela, diálogos e sinais de intenção do usuário."""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dlpdownloader.config.interface import ALTURA, LARGURA, TEXTOS, TITULO
from dlpdownloader.config.perfis import PERFIS
from dlpdownloader.visoes.dialogo_progresso import DialogoProgresso


class JanelaPrincipal(QMainWindow):
    """View passiva; não importa Model, serviço ou Controller."""

    download_solicitado = pyqtSignal(str, str, object, str)
    pasta_solicitada = pyqtSignal()
    fechamento_solicitado = pyqtSignal()

    def __init__(self, icone: Path):
        super().__init__()
        self.setWindowTitle(TITULO)
        self.setWindowIcon(QIcon(str(icone)))
        self.setMinimumSize(LARGURA, ALTURA)
        self._ocupada = False
        self._pode_fechar = False
        self.popup = None
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 24)
        subtitulo = QLabel(TEXTOS["subtitulo"])
        subtitulo.setObjectName("subtitulo")
        layout.addWidget(subtitulo)
        formulario = QFormLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText(TEXTOS["placeholder"])
        self.formato = QComboBox()
        for identificador, rotulo, *_ in PERFIS:
            self.formato.addItem(rotulo, identificador)
        self.bitrate = QComboBox()
        self.rotulo_bitrate = QLabel(TEXTOS["bitrate"])
        self.ajuda = QLabel()
        self.ajuda.setWordWrap(True)
        self.destino = QLineEdit()
        self.destino.setReadOnly(True)
        self.escolher = QPushButton(TEXTOS["escolher"])
        linha_destino = QHBoxLayout()
        linha_destino.addWidget(self.destino, 1)
        linha_destino.addWidget(self.escolher)
        formulario.addRow(TEXTOS["link"], self.url)
        formulario.addRow(TEXTOS["formato"], self.formato)
        formulario.addRow(self.rotulo_bitrate, self.bitrate)
        formulario.addRow(self.ajuda)
        formulario.addRow(TEXTOS["destino"], linha_destino)
        layout.addLayout(formulario)
        layout.addStretch()
        self.baixar = QPushButton(TEXTOS["baixar"])
        self.baixar.setObjectName("principal")
        layout.addWidget(self.baixar)
        self.status = QLabel(TEXTOS["verificando"])
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.baixar.clicked.connect(self._solicitar_download)
        self.url.returnPressed.connect(self._solicitar_download)
        self.escolher.clicked.connect(self._solicitar_pasta)
        self.formato.currentIndexChanged.connect(self._atualizar_perfil)
        self._atualizar_perfil()

    def _atualizar_perfil(self) -> None:
        perfil = PERFIS[self.formato.currentIndex()]
        self.bitrate.clear()
        for valor in perfil[3]:
            rotulo = TEXTOS["original"] if valor is None else TEXTOS["kbps"].format(valor=valor)
            self.bitrate.addItem(rotulo, valor)
        self.definir_visibilidade_bitrate(bool(perfil[3]))
        self.ajuda.setText(perfil[4])

    def definir_visibilidade_bitrate(self, visivel: bool) -> None:
        """Única fonte da visibilidade do campo condicional."""
        self.bitrate.setVisible(visivel)
        self.rotulo_bitrate.setVisible(visivel)

    def esta_bitrate_visivel(self) -> bool:
        """Consulta independente de a janela já ter sido exibida."""
        return not self.bitrate.isHidden()

    def _solicitar_download(self) -> None:
        if not self._ocupada and self.baixar.isEnabled():
            self.download_solicitado.emit(
                self.url.text().strip(),
                self.formato.currentData(),
                self.bitrate.currentData(),
                self.destino.text(),
            )

    def _solicitar_pasta(self) -> None:
        if not self._ocupada:
            self.pasta_solicitada.emit()

    def definir_ocupada(self, ocupada: bool, disponivel: bool = True) -> None:
        """Bloqueia entradas e preserva o bloqueio por falta de ferramentas."""
        self._ocupada = ocupada
        for widget in (self.url, self.formato, self.bitrate, self.escolher):
            widget.setEnabled(not ocupada)
        self.baixar.setEnabled(not ocupada and disponivel)

    def atualizar_status(self, texto: str) -> None:
        """Mostra aviso não bloqueante."""
        self.status.setText(texto)

    def definir_destino(self, caminho: str) -> None:
        """Exibe o diretório restaurado ou selecionado."""
        self.destino.setText(caminho)

    def escolher_diretorio(self, inicial: str) -> str:
        """Devolve string vazia quando o usuário cancela o seletor."""
        return QFileDialog.getExistingDirectory(self, TEXTOS["escolher"], inicial)

    def exibir_erro(self, mensagem: str) -> None:
        """Exibe falha com vínculo à janela principal."""
        QMessageBox.critical(self, TITULO, mensagem)

    def exibir_sucesso(self, caminho: str) -> None:
        """Confirma o caminho final da operação."""
        QMessageBox.information(
            self, TITULO, f"{TEXTOS['dl_concluido']}\n{TEXTOS['sucesso'].format(caminho=caminho)}"
        )

    def perguntar_substituicao(self) -> bool:
        """Confirma explicitamente a substituição de um arquivo existente."""
        caixa = QMessageBox(self)
        caixa.setWindowTitle(TITULO)
        caixa.setText(TEXTOS["confirmar_substituicao"])
        sim = caixa.addButton(TEXTOS["sim"], QMessageBox.ButtonRole.YesRole)
        nao = caixa.addButton(TEXTOS["nao"], QMessageBox.ButtonRole.NoRole)
        caixa.setDefaultButton(nao)
        caixa.exec()
        return caixa.clickedButton() == sim

    def perguntar_fechamento(self) -> bool:
        """Pede confirmação apenas durante uma operação ativa."""
        caixa = QMessageBox(self)
        caixa.setWindowTitle(TITULO)
        caixa.setText(TEXTOS["fechar"])
        sim = caixa.addButton(TEXTOS["sim"], QMessageBox.ButtonRole.YesRole)
        nao = caixa.addButton(TEXTOS["nao"], QMessageBox.ButtonRole.NoRole)
        caixa.setDefaultButton(nao)
        caixa.exec()
        return caixa.clickedButton() == sim

    def exibir_progresso(self, cancelar) -> None:
        """Abre popup sem executar trabalho na thread da GUI."""
        self.popup = DialogoProgresso(self)
        self.popup.cancelamento_solicitado.connect(cancelar)
        self.popup.show()

    def atualizar_progresso(self, etapa: str, percentual: int, detalhes: str) -> None:
        """Atualiza widgets somente no contexto da GUI."""
        if self.popup:
            self.popup.atualizar(etapa, percentual, detalhes)

    def definir_cancelando(self) -> None:
        """Atualiza o popup para o encerramento em andamento."""
        if self.popup:
            self.popup.definir_cancelando()

    def finalizar_progresso(self) -> None:
        """Libera o popup após o trabalho finalizar."""
        if self.popup:
            self.popup.finalizar()
            self.popup.deleteLater()
            self.popup = None

    def permitir_fechamento(self) -> None:
        """Fecha após confirmação de que não há threads ativas."""
        self._pode_fechar = True
        self.close()

    def closeEvent(self, evento: QCloseEvent) -> None:
        if self._pode_fechar:
            evento.accept()
        else:
            evento.ignore()
            self.fechamento_solicitado.emit()
