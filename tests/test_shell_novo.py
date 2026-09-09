"""A casca nova, no que dá para exercitar sem câmera nem OBS. Ver D-52.

O caso do preview existe por um bug real: `_AdaptadorPreview.size()` devolvia um objeto com
`width()` e `height()` em vez de um `QSize`. O binding do PySide6 casa a assinatura por
**tipo**, não por interface, então `QPixmap.scaled()` recusava com `TypeError` — a cada
quadro, ou seja, traceback em loop no console assim que a câmera ligava.

O smoke de QML não pegava: ele confirma que a tela **carrega**, e o preview só quebra
quando um quadro **passa**. É a diferença entre montar a tubulação e abrir a água.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication

from core.estado_app import EstadoApp


GESTOS = [("V", ""), ("Joinha", ""), ("Punho", "")]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def casca(app):
    from ui.shell_novo import ShellNovo

    estado = EstadoApp({}, [nome for nome, _ in GESTOS])
    return ShellNovo(estado, GESTOS)


def test_preview_devolve_qsize_de_verdade(casca):
    """O `QPixmap.scaled` de `MainWindow.update_frame` exige `QSize`, não um pato."""
    assert isinstance(casca.preview_label.size(), QSize)


def test_um_quadro_atravessa_o_caminho_do_preview(casca):
    """Reproduz `MainWindow.update_frame` sem câmera: o `scaled` tem de aceitar o tamanho."""
    imagem = QImage(64, 48, QImage.Format_RGB888)
    imagem.fill(Qt.black)

    # A linha que quebrava, com os mesmos argumentos da janela.
    escalada = QPixmap.fromImage(imagem).scaled(
        casca.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    casca.preview_label.setPixmap(escalada)

    assert casca.shell.temFrame
    assert casca.shell.contadorDeFrames == 1


def test_contador_avanca_a_cada_quadro(casca):
    """Sem contador novo a `Image` do QML reusaria a URL em cache e o preview congelaria."""
    imagem = QImage(8, 8, QImage.Format_RGB888)
    imagem.fill(Qt.black)
    pixmap = QPixmap.fromImage(imagem)

    for esperado in (1, 2, 3):
        casca.preview_label.setPixmap(pixmap)
        assert casca.shell.contadorDeFrames == esperado


def test_limpar_apaga_o_frame(casca):
    imagem = QImage(8, 8, QImage.Format_RGB888)
    imagem.fill(Qt.black)
    casca.preview_label.setPixmap(QPixmap.fromImage(imagem))
    assert casca.shell.temFrame

    casca.preview_label.clear()
    assert not casca.shell.temFrame


def test_qml_informa_o_tamanho_do_preview(casca):
    casca.shell.definirTamanhoDoPreview(320, 180)
    assert casca.preview_label.size() == QSize(320, 180)


def test_tamanho_invalido_e_ignorado(casca):
    """Durante o layout o QML passa 0 antes de ter geometria; reduzir a zero mata o quadro."""
    antes = casca.preview_label.size()
    casca.shell.definirTamanhoDoPreview(0, 0)
    assert casca.preview_label.size() == antes


def test_chip_de_estado_so_aceita_estado_da_engine(casca):
    """"Config salva!" não pode apagar "Rodando" do chip. Ver `_AdaptadorStatus`."""
    casca.status_label.setText("Status: Rodando")
    assert casca.shell.estadoTexto == "Rodando"
    assert casca.shell.rodando

    casca.status_label.setText("Config salva!")
    assert casca.shell.estadoTexto == "Rodando"
    assert casca.shell.rodando

    casca.status_label.setText("Status: Parado")
    assert casca.shell.estadoTexto == "Parado"
    assert not casca.shell.rodando


def test_estado_do_obs_nao_viaja_dentro_do_emoji(casca):
    """O rodapé de Widgets manda "🟢 OBS: Conectado"; o emoji não passa da fronteira."""
    casca.obs_footer_label.setText("🟢 OBS: Conectado")
    assert casca.shell.obsConectado
    assert "🟢" not in casca.shell.obsTexto

    casca.obs_footer_label.setText("🔴 OBS: Offline")
    assert not casca.shell.obsConectado


def test_botao_unico_reflete_o_enabled_dos_dois(casca):
    """A casca tem um botão que alterna; o mixin continua falando com start e stop."""
    casca.start_button.setEnabled(False)
    casca.stop_button.setEnabled(True)
    assert not casca.shell.podeIniciar
    assert casca.shell.podeParar


def test_resumo_do_cartao_le_o_binding(casca):
    """O cartão diz o que o gesto faz sem precisar de clique."""
    casca._estado.definir_binding("V", use_scene=True, scene="Gameplay")
    assert casca.ponte_gestos._resumo("V") == "Cena: Gameplay"

    casca._estado.definir_binding("V", use_hotkey=True, hotkey="Ctrl+F5")
    assert casca.ponte_gestos._resumo("V") == "Cena: Gameplay · Ctrl+F5"


def test_grade_nova_traz_os_gestos_inativos(casca):
    """A grade antiga recebe só os ativos; a nova mostra os doze com o estado junto."""
    nomes = [g["nome"] for g in casca.ponte_gestos.todosOsGestos]
    assert nomes == [nome for nome, _ in GESTOS]

    ativos = {g["nome"]: g["ativo"] for g in casca.ponte_gestos.todosOsGestos}
    assert ativos["V"] is True
