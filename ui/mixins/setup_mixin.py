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

from ui import vinculo
from ui.tabs.geral_tab import GeralTab
from ui.tabs.gestos_tab import GestosTab
from ui.tabs.obs_tab import OBSTab
from util.logger import get_logger

logger = get_logger(__name__)


def _construir_aba_geral(estado):
    """A aba Geral é QML por padrão. `GESTURENODE_UI=widgets` volta à antiga. Ver D-49.

    A saída de emergência existe porque a versão QML é nova e só se prova em uso: se ela
    falhar na máquina de alguém, esse alguém precisa de um caminho para continuar
    trabalhando que não seja editar código. As duas cumprem `ui/tabs/geral_contrato.py`,
    então nada além desta função sabe qual está montada.
    """
    if os.environ.get("GESTURENODE_UI", "").strip().lower() == "widgets":
        return GeralTab(estado)

    try:
        from ui.tabs.geral_tab_qml import GeralTabQml

        return GeralTabQml(estado)
    except Exception:
        # Um QtQuick indisponível não pode impedir o app de abrir — a aba antiga serve.
        logger.exception("Falha ao carregar a aba Geral em QML; usando a de Widgets")
        return GeralTab(estado)


class SetupMixin:

    def _setup_ui(self):
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
        self.gestos_tab = GestosTab()
        self.obs_tab = OBSTab()

        self.tabs.addTab(self.geral_tab, "Geral")
        self.tabs.addTab(self.gestos_tab, "Gestos")
        self.tabs.addTab(self.obs_tab, "OBS")

        # Os aliases da aba Geral saíram: ela agora fala pelo contrato, e alcançar os
        # widgets dela era justamente o que amarrava a janela a uma implementação.
        self.grid_layout = self.gestos_tab.grid_layout
        self.choose_gestures_button = self.gestos_tab.choose_gestures_button
        self.selected_gesture_label = self.gestos_tab.selected_gesture_label
        self.hold_slider = self.gestos_tab.hold_slider
        self.hold_value_spinbox = self.gestos_tab.hold_value_spinbox
        self.cooldown_slider = self.gestos_tab.cooldown_slider
        self.cooldown_value_spinbox = self.gestos_tab.cooldown_value_spinbox
        self.scene_action_checkbox = self.gestos_tab.scene_action_checkbox
        self.sound_action_checkbox = self.gestos_tab.sound_action_checkbox
        self.hotkey_action_checkbox = self.gestos_tab.hotkey_action_checkbox
        self.scene_row = self.gestos_tab.scene_row
        self.sound_row = self.gestos_tab.sound_row
        self.hotkey_row = self.gestos_tab.hotkey_row
        self.scene_edit = self.gestos_tab.scene_edit
        self.sound_file_edit = self.gestos_tab.sound_file_edit
        self.hotkey_edit = self.gestos_tab.hotkey_edit
        self.browse_sound_button = self.gestos_tab.browse_sound_button

        self.obs_host = self.obs_tab.obs_host
        self.obs_port = self.obs_tab.obs_port
        self.obs_password = self.obs_tab.obs_password
        self.test_obs_button = self.obs_tab.test_obs_button
        self.obs_status_label = self.obs_tab.obs_status_label

        # A aba Geral fala por intenção, não por widget. Ver `ui/tabs/geral_contrato.py`.
        self.geral_tab.modoPedido.connect(self.on_modo_changed)
        self.geral_tab.maosPedidas.connect(self.on_max_maos_changed)
        self.geral_tab.resolucaoPedida.connect(self.on_resolution_changed)
        self.geral_tab.fpsPedido.connect(self.on_fps_changed)
        self.geral_tab.cameraPedida.connect(self.on_camera_changed)
        self.geral_tab.esqueletoPedido.connect(self.on_esqueleto_changed)
        self.geral_tab.recomendadoPedido.connect(self.aplicar_preset_recomendado)
        self.choose_gestures_button.clicked.connect(self.open_gesture_selector_dialog)
        # O espelho slider↔spin sai daqui: `vinculo.espelhar` faz o que os quatro
        # handlers `on_*_changed` faziam, com a guarda de sinais num lugar só. Ver D-47.
        vinculo.espelhar(self.hold_slider, self.hold_value_spinbox)
        vinculo.espelhar(self.cooldown_slider, self.cooldown_value_spinbox)

        # Um handler por controle, não três. `on_dynamic_setting_changed` já grava
        # hold/cooldown e reconfigura a engine viva — que é tudo que mover um slider muda.
        for controle in (
            self.hold_slider,
            self.hold_value_spinbox,
            self.cooldown_slider,
            self.cooldown_value_spinbox,
        ):
            controle.valueChanged.connect(self.on_dynamic_setting_changed)

        self.scene_action_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.sound_action_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.hotkey_action_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.scene_edit.textChanged.connect(self.on_current_gesture_changed)
        self.sound_file_edit.textChanged.connect(self.on_current_gesture_changed)
        self.hotkey_edit.textChanged.connect(self.on_current_gesture_changed)
        self.hotkey_edit.hotkeyCommitted.connect(self.on_current_gesture_changed)
        self.browse_sound_button.clicked.connect(self.select_sound_file)

        self.obs_host.textChanged.connect(self.on_obs_changed)
        self.obs_port.valueChanged.connect(self.on_obs_changed)
        self.obs_password.textChanged.connect(self.on_obs_changed)
        self.test_obs_button.clicked.connect(self.testar_conexao_obs)

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
