from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import os

from ui.tabs.geral_tab import GeralTab
from ui.tabs.gestos_tab import GestosTab
from ui.tabs.obs_tab import OBSTab
from util.logger import get_logger

logger = get_logger(__name__)


# Abas que caíram para a versão antiga por falha ao carregar o QML. Ver D-49.
#
# O log sozinho não basta: empacotado, o app roda sem console, então a mensagem não chega
# a lugar nenhum. O usuário veria a interface antiga achando que era a nova, e nós
# perderíamos horas procurando um problema no QML que na verdade seria de empacotamento.
# Mesma regra do D-29 e do D-39: degradação silenciosa é pior que degradação anunciada.
_QUEDAS = []


def _escolha_de_interface():
    return os.environ.get("GESTURENODE_UI", "").strip().lower()


def _usar_widgets():
    return _escolha_de_interface() == "widgets"


def _usar_nova():
    """A casca remodelada. Ver D-52.

    Vale a mesma regra do D-49: é opção, não substituição. Enquanto a interface nova não
    tiver rodado o suficiente em uso real, quem estiver com ela na frente precisa de um
    caminho de volta que não seja editar código — e quem não pedir continua na de abas.
    """
    return _escolha_de_interface() == "novo"


def _cair_para_widgets(aba, erro):
    logger.exception("Falha ao carregar a aba %s em QML; usando a de Widgets", aba)
    _QUEDAS.append(f"Aba {aba}: interface nova indisponível ({erro}); usando a antiga.")


def _construir_aba_gestos(estado):
    if _usar_widgets():
        return GestosTab(estado)
    try:
        from ui.tabs.gestos_tab_qml import GestosTabQml

        return GestosTabQml(estado)
    except Exception as exc:
        _cair_para_widgets("Gestos", exc)
        return GestosTab(estado)


def _construir_aba_obs(estado):
    """Mesma escolha e mesma rede de segurança da aba Geral."""
    if _usar_widgets():
        return OBSTab(estado)
    try:
        from ui.tabs.obs_tab_qml import ObsTabQml

        return ObsTabQml(estado)
    except Exception as exc:
        _cair_para_widgets("OBS", exc)
        return OBSTab(estado)


def _construir_aba_geral(estado):
    """A aba Geral é QML por padrão. `GESTURENODE_UI=widgets` volta à antiga. Ver D-49.

    A saída de emergência existe porque a versão QML é nova e só se prova em uso: se ela
    falhar na máquina de alguém, esse alguém precisa de um caminho para continuar
    trabalhando que não seja editar código. As duas cumprem `ui/tabs/geral_contrato.py`,
    então nada além desta função sabe qual está montada.
    """
    if _usar_widgets():
        return GeralTab(estado)

    try:
        from ui.tabs.geral_tab_qml import GeralTabQml

        return GeralTabQml(estado)
    except Exception as exc:
        # Um QtQuick indisponível não pode impedir o app de abrir — a aba antiga serve.
        _cair_para_widgets("Geral", exc)
        return GeralTab(estado)


class SetupMixin:

    @staticmethod
    def quedas_de_interface():
        """O que caiu para a versão antiga. A janela relata depois que o log existe."""
        return list(_QUEDAS)

    def _montar_interface_nova(self):
        """A casca remodelada, no lugar do `QTabWidget`. Ver D-52.

        Os mixins não sabem que ela existe: a casca oferece `geral_tab`, `gestos_tab`,
        `obs_tab`, `preview_label`, `log_view` e os três botões com a mesma superfície de
        sempre, e traduz para as pontes. Ver o cabeçalho de `ui/shell_novo.py`.
        """
        from ui.shell_novo import ShellNovo

        # A grade nova mostra os doze, não só os ativos — o interruptor mora no cartão.
        todos = [
            (nome, self._resolve_asset_path(icone)) for nome, icone in self.ALL_GESTURES
        ]
        self.shell = ShellNovo(self.estado, todos)
        self.setCentralWidget(self.shell)

        # O piso de 1200x760 da janela é da interface de abas, onde o `QFormLayout` não
        # tem ponto de quebra e espremer a coluna quebra a tela. A casca nova tem quebra
        # de verdade — o painel de preview colapsa e a tela de Gestos empilha —, então o
        # piso pode baixar.
        #
        # Isto não é detalhe: num laptop de 1366x768, a barra de tarefas deixa ~728px de
        # altura útil. Com o piso em 760 a janela **não cabe na tela**, e o usuário não
        # tem como diminuir. Verificado de 1366x728 até 760x520 sem sobreposição.
        self.setMinimumSize(940, 600)

        # Os mesmos atributos que a janela de abas publica, para os mixins não mudarem.
        self.geral_tab = self.shell.geral_tab
        self.gestos_tab = self.shell.gestos_tab
        self.obs_tab = self.shell.obs_tab
        self.sobre_tab = None
        self.preview_label = self.shell.preview_label
        self.status_label = self.shell.status_label
        self.obs_footer_label = self.shell.obs_footer_label
        self.log_view = self.shell.log_view
        self.start_button = self.shell.start_button
        self.stop_button = self.shell.stop_button
        self.restart_button = self.shell.restart_button

        self.start_button.clicked.connect(self.start_engine)
        self.stop_button.clicked.connect(self.stop_engine)
        self.restart_button.clicked.connect(self.restart_engine)
        self.stop_button.setEnabled(False)

        # As mesmas intenções das abas, vindas da casca.
        self.shell.modoPedido.connect(self.on_modo_changed)
        self.shell.maosPedidas.connect(self.on_max_maos_changed)
        self.shell.resolucaoPedida.connect(self.on_resolution_changed)
        self.shell.fpsPedido.connect(self.on_fps_changed)
        self.shell.cameraPedida.connect(self.on_camera_changed)
        self.shell.esqueletoPedido.connect(self.on_esqueleto_changed)
        self.shell.recomendadoPedido.connect(self.aplicar_preset_recomendado)

        self.shell.procurarSomPedido.connect(self.select_sound_file)
        self.shell.bindingEditado.connect(self.on_current_gesture_changed)
        self.shell.gestoSelecionado.connect(self.ao_selecionar_gesto)
        # Ligar e desligar o gesto acontece no cartão da grade. `escolherGestosPedido`
        # **não** é ligado aqui de propósito: o diálogo `open_gesture_selector_dialog` é
        # Widgets, e um `QDialog` cinza abrindo por cima desta interface seria a costura
        # que a remodelagem existe para fechar. Nesta casca ele não tem função — a grade
        # mostra os doze gestos e cada cartão tem o próprio interruptor.
        self.shell.ativoAlternado.connect(self.ao_alternar_gesto_ativo)

        self.shell.credenciaisMudaram.connect(self.on_obs_changed)
        self.shell.testePedido.connect(self.testar_conexao_obs)

        self._populate_camera_devices()


    def _setup_ui(self):
        if _usar_nova():
            try:
                self._montar_interface_nova()
                return
            except Exception as exc:
                # Mesma rede do D-49: a casca nova falhar não pode impedir o app de abrir,
                # e a queda tem de ser anunciada — empacotado não há console.
                _cair_para_widgets("Interface nova", exc)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter)

        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        self.tabs = QTabWidget()
        left_layout.addWidget(self.tabs)

        self.geral_tab = _construir_aba_geral(self.estado)
        self.gestos_tab = _construir_aba_gestos(self.estado)
        self.obs_tab = _construir_aba_obs(self.estado)

        self.tabs.addTab(self.geral_tab, "Geral")
        self.tabs.addTab(self.gestos_tab, "Gestos")
        self.tabs.addTab(self.obs_tab, "OBS")

        # A Sobre é opcional: sem estado para refletir, se o QML falhar ela some em vez de
        # impedir o app de abrir. É a única aba de que se pode abrir mão. Ver D-51.
        try:
            from ui.tabs.sobre_tab_qml import SobreTabQml

            self.sobre_tab = SobreTabQml()
            self.tabs.addTab(self.sobre_tab, "Sobre")
        except Exception:
            logger.exception("Aba Sobre indisponível; seguindo sem ela")
            self.sobre_tab = None

        # Os aliases da aba Geral saíram: ela agora fala pelo contrato, e alcançar os
        # widgets dela era justamente o que amarrava a janela a uma implementação.


        # A aba Geral fala por intenção, não por widget. Ver `ui/tabs/geral_contrato.py`.
        self.geral_tab.modoPedido.connect(self.on_modo_changed)
        self.geral_tab.maosPedidas.connect(self.on_max_maos_changed)
        self.geral_tab.resolucaoPedida.connect(self.on_resolution_changed)
        self.geral_tab.fpsPedido.connect(self.on_fps_changed)
        self.geral_tab.cameraPedida.connect(self.on_camera_changed)
        self.geral_tab.esqueletoPedido.connect(self.on_esqueleto_changed)
        self.geral_tab.recomendadoPedido.connect(self.aplicar_preset_recomendado)
        # A aba Gestos também. O espelho slider↔spin e os oito `connect` por campo
        # sumiram: quem grava agora é a aba, que avisa uma vez que editou.
        self.gestos_tab.escolherGestosPedido.connect(self.open_gesture_selector_dialog)
        self.gestos_tab.procurarSomPedido.connect(self.select_sound_file)
        self.gestos_tab.bindingEditado.connect(self.on_current_gesture_changed)
        self.gestos_tab.gestoSelecionado.connect(self.ao_selecionar_gesto)

        # A aba OBS também fala por intenção.
        self.obs_tab.credenciaisMudaram.connect(self.on_obs_changed)
        self.obs_tab.testePedido.connect(self.testar_conexao_obs)

        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        right_title = QLabel("Preview")
        right_title.setObjectName("title")
        right_layout.addWidget(right_title)

        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(360)
        self.preview_label.setStyleSheet("background-color: #0d0d0d; border: 1px solid #2d2d2d; border-radius: 8px;")
        right_layout.addWidget(self.preview_label, stretch=1)

        bottom_panel = QFrame()
        bottom_panel.setObjectName("bottomPanel")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(8)

        controls_layout = QHBoxLayout()
        bottom_layout.addLayout(controls_layout)

        self.start_button = QPushButton("Iniciar")
        self.start_button.setObjectName("primary")
        self.stop_button = QPushButton("Parar")
        self.stop_button.setObjectName("danger")
        self.restart_button = QPushButton("Reiniciar")
        self.restart_button.setObjectName("warning")
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_engine)
        self.stop_button.clicked.connect(self.stop_engine)
        self.restart_button.clicked.connect(self.restart_engine)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.restart_button)

        self.status_label = QLabel("Status: Parado")
        self.obs_footer_label = QLabel("🔴 OBS: Desconectado")
        status_row = QHBoxLayout()
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_row.addWidget(self.obs_footer_label)
        bottom_layout.addLayout(status_row)

        log_title = QLabel("Logs")
        log_title.setObjectName("title")
        bottom_layout.addWidget(log_title)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setMaximumBlockCount(300)
        self.log_view.setMinimumHeight(120)
        bottom_layout.addWidget(self.log_view)

        right_layout.addWidget(bottom_panel, stretch=0)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([520, 680])

        self._populate_camera_devices()
