"""Sinais, estados, persistência e vida útil de threads com GUI offscreen."""

import threading
from pathlib import Path

from PyQt6.QtCore import QTimer

from dlpdownloader.controladores.download import ControladorDownload
from dlpdownloader.modelos.download import Estado
from dlpdownloader.modelos.erros import Cancelado, ErroDependencia
from dlpdownloader.modelos.progresso import EventoProgresso
from dlpdownloader.servicos.preferencias import Preferencias


def preparar(janela, tmp_path, servico, verificar=lambda evento: object()):
    preferencias = Preferencias(tmp_path / "dados/config.json", tmp_path)
    return ControladorDownload(janela, preferencias, verificar, lambda ferramentas: servico)


def test_bitrate_condicional_limpa_valor_e_icone_presente(janela):
    assert not janela.windowIcon().isNull()
    assert not janela.esta_bitrate_visivel()
    janela.formato.setCurrentIndex(janela.formato.findData("mp3"))
    assert janela.esta_bitrate_visivel() and janela.bitrate.currentData() == 128
    janela.formato.setCurrentIndex(janela.formato.findData("flac"))
    assert not janela.esta_bitrate_visivel() and janela.bitrate.currentData() is None


def test_cancelar_seletor_nao_altera_preferencias(janela, tmp_path):
    controlador = preparar(janela, tmp_path, None)
    janela.definir_destino(str(tmp_path))
    janela.escolher_diretorio = lambda inicial: ""
    controlador.escolher_pasta()
    assert janela.destino.text() == str(tmp_path)
    assert not controlador.preferencias.arquivo.exists()


def test_pasta_escolhida_persiste_imediatamente(janela, tmp_path):
    controlador = preparar(janela, tmp_path, None)
    janela.escolher_diretorio = lambda inicial: str(tmp_path)
    controlador.escolher_pasta()
    assert controlador.preferencias.carregar()[0] == tmp_path


def test_ambiente_ausente_bloqueia_download_mas_restaura_destino(janela, tmp_path, qtbot):
    def ausente(evento):
        raise ErroDependencia("ausente")

    controlador = preparar(janela, tmp_path, None, ausente)
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert controlador.estado == Estado.INDISPONIVEL
    assert not janela.baixar.isEnabled()
    assert janela.destino.text() == str(tmp_path)


def test_ferramentas_ausentes_recusa_reparo_exibe_aviso(janela, tmp_path, qtbot):
    def ausente(evento):
        raise ErroDependencia("ausente")

    avisos = []
    janela.perguntar_reparo = lambda: False
    janela.avisar_reparo_manual = lambda: avisos.append(True)
    controlador = preparar(janela, tmp_path, None, ausente)
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert avisos == [True] and janela.status.text() == ""
    assert controlador.estado == Estado.INDISPONIVEL and not janela.baixar.isEnabled()


def test_ferramentas_ausentes_aceita_reparo_fecha_app(janela, tmp_path, qtbot):
    def ausente(evento):
        raise ErroDependencia("ausente")

    acoes = []
    janela.perguntar_reparo = lambda: True
    janela.permitir_fechamento = lambda: acoes.append("fechou")
    preferencias = Preferencias(tmp_path / "dados/config.json", tmp_path)
    controlador = ControladorDownload(
        janela,
        preferencias,
        ausente,
        lambda ferramentas: None,
        lambda: acoes.append("solicitou") or True,
    )
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert acoes == ["solicitou", "fechou"] and janela.status.text() == ""


def test_reparador_ausente_mostra_erro_e_preserva_janela(janela, tmp_path, qtbot):
    def ausente(evento):
        raise ErroDependencia("ausente")

    erros = []
    janela.perguntar_reparo = lambda: True
    janela.exibir_erro = erros.append
    fechamentos = []
    janela.permitir_fechamento = lambda: fechamentos.append(True)
    controlador = preparar(janela, tmp_path, None, ausente)
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert erros and "repair.exe" in erros[0] and not fechamentos


def test_dialogo_reparo_mostra_pergunta_e_responde_sim_nao(janela):
    from PyQt6.QtWidgets import QApplication, QMessageBox

    from dlpdownloader.config.interface import TEXTOS

    for texto, esperado in [(TEXTOS["sim"], True), (TEXTOS["nao"], False)]:

        def responder():
            caixa = QApplication.activeModalWidget()
            assert caixa.icon() == QMessageBox.Icon.Critical
            assert caixa.text() == TEXTOS["perguntar_reparo"]
            next(b for b in caixa.buttons() if b.text() == texto).click()

        QTimer.singleShot(0, responder)
        assert type(janela).perguntar_reparo(janela) is esperado


def test_trabalho_nao_bloqueia_gui_e_ignora_inicio_duplicado(janela, tmp_path, qtbot):
    liberar = threading.Event()
    chamadas = []

    class Servico:
        def baixar(self, pedido, cancelar, progresso, confirmar):
            chamadas.append(threading.get_ident())
            progresso(EventoProgresso("baixando", "299", 50, 100))
            if not liberar.wait(5):
                raise RuntimeError("O timer da GUI não executou")
            return Path(tmp_path / "resultado.mp4")

    controlador = preparar(janela, tmp_path, Servico())
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    argumentos = ("https://example.com/v", "mp4", None, str(tmp_path))
    controlador.iniciar(*argumentos)
    controlador.iniciar(*argumentos)
    QTimer.singleShot(20, liberar.set)
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert controlador.estado == Estado.PRONTO
    assert len(chamadas) == 1 and chamadas[0] != threading.get_ident()
    assert janela.popup is None and janela.baixar.isEnabled()


def test_cancelamento_e_cleanup_sem_sucesso(janela, tmp_path, qtbot):
    iniciou = threading.Event()
    sucessos = []
    janela.exibir_sucesso = sucessos.append

    class Servico:
        def baixar(self, pedido, cancelar, progresso, confirmar):
            iniciou.set()
            cancelar.wait(5)
            raise Cancelado()

    controlador = preparar(janela, tmp_path, Servico())
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    controlador.iniciar("https://example.com", "mp4", None, str(tmp_path))
    qtbot.waitUntil(iniciou.is_set)
    controlador.cancelar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert not sucessos and controlador.estado == Estado.PRONTO
    assert janela.popup is None


def test_erro_apos_progresso_nao_gera_sucesso(janela, tmp_path, qtbot):
    from dlpdownloader.modelos.erros import ErroDownload

    sucessos, erros = [], []
    janela.exibir_sucesso = sucessos.append
    janela.exibir_erro = erros.append

    class Servico:
        def baixar(self, pedido, cancelar, progresso, confirmar):
            progresso(EventoProgresso("baixando", "video", 100, 100))
            progresso(EventoProgresso("finalizando"))
            raise ErroDownload("Falha na junção")

    controlador = preparar(janela, tmp_path, Servico())
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    controlador.iniciar("https://example.com", "mp4", None, str(tmp_path))
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert erros == ["Falha na junção"] and not sucessos
    assert janela.baixar.isEnabled() and controlador.estado == Estado.PRONTO


def test_fechar_aguarda_cancelamento_do_trabalho(janela, tmp_path, qtbot):
    iniciou = threading.Event()
    fechamentos = []
    janela.perguntar_fechamento = lambda: True
    janela.permitir_fechamento = lambda: fechamentos.append(True)

    class Servico:
        def baixar(self, pedido, cancelar, progresso, confirmar):
            iniciou.set()
            cancelar.wait(5)
            raise Cancelado()

    controlador = preparar(janela, tmp_path, Servico())
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    controlador.iniciar("https://example.com", "mp4", None, str(tmp_path))
    qtbot.waitUntil(iniciou.is_set)
    controlador.fechar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert fechamentos == [True] and janela.popup is None


def test_confirmacao_de_substituicao_e_mensagem_de_sucesso(janela, tmp_path, qtbot):
    from dlpdownloader.config.interface import TEXTOS

    sucessos = []
    janela.exibir_sucesso = sucessos.append
    janela.perguntar_substituicao = lambda: True

    class Servico:
        def baixar(self, pedido, cancelar, progresso, confirmar):
            assert confirmar()
            return tmp_path / "resultado.mp4"

    controlador = preparar(janela, tmp_path, Servico())
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    controlador.iniciar("https://example.com", "mp4", None, str(tmp_path))
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert sucessos == [str(tmp_path / "resultado.mp4")]
    assert janela.status.text().startswith(TEXTOS["dl_concluido"] + "\n")


def test_recusa_de_substituicao_retorna_ao_menu(janela, tmp_path, qtbot):
    from dlpdownloader.config.interface import TEXTOS
    from dlpdownloader.modelos.erros import SubstituicaoRecusada

    erros = []
    janela.exibir_erro = erros.append
    janela.perguntar_substituicao = lambda: False

    class Servico:
        def baixar(self, pedido, cancelar, progresso, confirmar):
            if not confirmar():
                raise SubstituicaoRecusada()

    controlador = preparar(janela, tmp_path, Servico())
    controlador.inicializar()
    qtbot.waitUntil(lambda: controlador.thread is None)
    controlador.iniciar("https://example.com", "mp4", None, str(tmp_path))
    qtbot.waitUntil(lambda: controlador.thread is None)
    assert not erros and janela.status.text() == TEXTOS["substituicao_recusada"]
    assert janela.baixar.isEnabled() and controlador.estado == Estado.PRONTO


def test_animacao_do_botao_preserva_clique_e_retorna(janela, qtbot):
    from PyQt6.QtCore import Qt

    janela.show()
    chamadas = []
    janela.baixar.clicked.connect(lambda: chamadas.append(True))
    qtbot.mouseClick(janela.baixar, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: janela.baixar.escala < 0.99)
    qtbot.waitUntil(lambda: janela.baixar.escala == 1.0)
    assert chamadas == [True]


def test_realce_da_selecao_acompanha_foco(janela, qtbot):
    janela.show()
    janela.formato.setFocus()
    qtbot.waitUntil(lambda: janela.formato.realce > 0.99)
    janela.url.setFocus()
    qtbot.waitUntil(lambda: janela.formato.realce < 0.01)


def test_menu_mantem_margem_proporcional(janela, qtbot):
    janela.show()
    janela.resize(800, 450)
    qtbot.waitUntil(
        lambda: janela._espaco_opcoes.width() == janela._barra_opcoes.sizeHint().width() + 80
    )
