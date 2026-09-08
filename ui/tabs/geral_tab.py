
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui import vinculo


class GeralTab(QWidget):
    def __init__(self):
        super().__init__()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        # Sem título "Configurações Gerais": a aba já se chama Geral. Repetir o nome
        # rouba uma linha para dizer o que o usuário acabou de clicar. Ver D-40.
        form = QFormLayout()
        form.setVerticalSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addLayout(form)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        mode_row = QWidget()
        mode_layout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(8)
        self.mode_test_button = QPushButton("Teste")
        self.mode_manual_button = QPushButton("Manual")
        self.mode_auto_button = QPushButton("Automático")
        for button in (self.mode_test_button, self.mode_manual_button, self.mode_auto_button):
            button.setObjectName("optionToggle")
            button.setCheckable(True)
            button.setMinimumWidth(92)
            button.setMinimumHeight(38)
            mode_layout.addWidget(button)
            self.mode_group.addButton(button)
        form.addRow("Modo:", mode_row)

        self.maos_group = QButtonGroup(self)
        self.maos_group.setExclusive(True)
        maos_row = QWidget()
        maos_layout = QHBoxLayout(maos_row)
        maos_layout.setContentsMargins(0, 0, 0, 0)
        maos_layout.setSpacing(8)
        self.maos_1_button = QPushButton("1 Mão")
        self.maos_2_button = QPushButton("2 Mãos")
        for button in (self.maos_1_button, self.maos_2_button):
            button.setObjectName("optionToggle")
            button.setCheckable(True)
            button.setMinimumWidth(92)
            button.setMinimumHeight(38)
            maos_layout.addWidget(button)
            self.maos_group.addButton(button)
        self.maos_1_button.setToolTip("Detecta apenas uma mão. Menor custo de CPU.")
        self.maos_2_button.setToolTip(
            "Detecta duas mãos simultaneamente. Qualquer mão pode acionar a mesma binding."
        )
        form.addRow("Mãos:", maos_row)

        self.mode_test_button.setToolTip(
            "Modo Teste: calibre gestos, câmera e ações sem executar nada — "
            "nenhum comando ao OBS, hotkey ou áudio."
        )
        self.mode_manual_button.setToolTip(
            "Modo Manual: conecta automaticamente ao OBS e executa hotkeys/áudio, "
            "mas mantém a câmera virtual desligada (para quem tem conflito de driver de VCam)."
        )
        self.mode_auto_button.setToolTip(
            "Modo Automático: gerencia conexão ao OBS e câmera virtual automaticamente ao iniciar."
        )

        # Uma linha, sobre o modo SELECIONADO — não as três de uma vez. Os outros dois já
        # se explicam pelo tooltip, e ninguém precisa ler sobre um modo que não escolheu.
        self.mode_help_label = QLabel("")
        self.mode_help_label.setObjectName("muted")
        self.mode_help_label.setWordWrap(True)
        layout.addWidget(self.mode_help_label)

        # Esqueleto vira par de toggles, no mesmo padrão visual de Modo e Mãos. Antes eram
        # dois checkboxes com rótulos de 30 e 40 caracteres; a forma já diz que são duas
        # saídas independentes, e "Preview"/"Saída OBS" bastam como palavra. Ver D-40.
        esqueleto_row = QWidget()
        esqueleto_layout = QHBoxLayout(esqueleto_row)
        esqueleto_layout.setContentsMargins(0, 0, 0, 0)
        esqueleto_layout.setSpacing(8)

        self.esqueleto_preview_button = QPushButton("Preview")
        self.esqueleto_preview_button.setToolTip(
            "Desenha o esqueleto da mão no preview desta janela, para ajustar posição e "
            "iluminação.\nNão altera o que sai para o OBS."
        )
        self.esqueleto_obs_button = QPushButton("Saída OBS")
        self.esqueleto_obs_button.setToolTip(
            "Desenha o esqueleto também na imagem enviada à câmera virtual — o público da "
            "live passa a ver as linhas da mão.\nNormalmente o esqueleto serve só para você."
        )
        for button in (self.esqueleto_preview_button, self.esqueleto_obs_button):
            button.setObjectName("optionToggle")
            button.setCheckable(True)
            button.setMinimumWidth(92)
            button.setMinimumHeight(38)
            esqueleto_layout.addWidget(button)

        form.addRow("Esqueleto:", esqueleto_row)

        camera_title = QLabel("Configuração da câmera")
        camera_title.setObjectName("sectionTitle")
        layout.addWidget(camera_title)

        camera_form = QFormLayout()
        camera_form.setVerticalSpacing(14)
        camera_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addLayout(camera_form)

        self.camera_device_combo = QComboBox()
        self.camera_device_combo.setToolTip("Selecione a câmera física usada para detecção dos gestos.")
        camera_form.addRow("Dispositivo:", self.camera_device_combo)

        # Aviso de incompatibilidade. Fica FORA do painel avançado de propósito: os botões
        # de resolução e FPS moram lá dentro, e o painel nasce recolhido — um aviso ali
        # dentro só apareceria para quem já foi procurar. Ver D-39.
        self.camera_aviso = QLabel("")
        self.camera_aviso.setObjectName("cameraAviso")
        self.camera_aviso.setWordWrap(True)
        self.camera_aviso.setVisible(False)
        # Paleta neutra do tema (fundo de card, borda padrão, texto secundário) e não a
        # âmbar de alerta que estava aqui. A faixa informa um fato do hardware, não uma
        # falha: o âmbar é reservado ao que o usuário precisa resolver. Ver D-45.
        self.camera_aviso.setStyleSheet(
            "QLabel#cameraAviso {"
            " background-color: #161616;"
            " border: 1px solid #2d2d2d;"
            " border-radius: 6px;"
            " padding: 10px;"
            " font-size: 14px;"
            " color: #a0a0a0; }"
        )
        layout.addWidget(self.camera_aviso)

        self.usar_recomendado_button = QPushButton("Usar configuração recomendada")
        self.usar_recomendado_button.setObjectName("ghost")
        self.usar_recomendado_button.setMinimumHeight(38)
        self.usar_recomendado_button.setVisible(False)
        layout.addWidget(self.usar_recomendado_button)

        # Painel colapsível de configurações avançadas
        self.advanced_toggle = QPushButton("Configurações Avançadas ▼")
        self.advanced_toggle.setObjectName("ghost")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        self.advanced_toggle.setMinimumHeight(38)
        self.advanced_toggle.clicked.connect(self._on_advanced_toggle)
        layout.addWidget(self.advanced_toggle)

        self.advanced_panel = QWidget()
        self.advanced_panel.setVisible(False)
        adv_layout = QVBoxLayout(self.advanced_panel)
        adv_layout.setContentsMargins(8, 4, 8, 4)
        adv_layout.setSpacing(10)

        adv_form = QFormLayout()
        adv_form.setVerticalSpacing(14)
        adv_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        adv_layout.addLayout(adv_form)

        self.resolution_group = QButtonGroup(self)
        self.resolution_group.setExclusive(True)
        self.resolution_buttons = {}
        resolution_row = QWidget()
        resolution_layout = QHBoxLayout(resolution_row)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(8)
        for label in ("480p", "720p", "1080p"):
            button = QPushButton(label)
            button.setObjectName("optionToggle")
            button.setCheckable(True)
            button.setMinimumWidth(92)
            button.setMinimumHeight(38)
            button.setToolTip(f"Define a resolução do preview e captura para {label}.")
            resolution_layout.addWidget(button)
            self.resolution_group.addButton(button)
            self.resolution_buttons[label] = button
        adv_form.addRow("Resolução:", resolution_row)

        self.fps_group = QButtonGroup(self)
        self.fps_group.setExclusive(True)
        self.fps_buttons = {}
        fps_row = QWidget()
        fps_layout = QHBoxLayout(fps_row)
        fps_layout.setContentsMargins(0, 0, 0, 0)
        fps_layout.setSpacing(8)
        for value in (30, 60):
            button = QPushButton(str(value))
            button.setObjectName("optionToggle")
            button.setCheckable(True)
            button.setMinimumWidth(92)
            button.setMinimumHeight(38)
            button.setToolTip(f"Define a taxa de quadros para {value} FPS.")
            fps_layout.addWidget(button)
            self.fps_group.addButton(button)
            self.fps_buttons[value] = button
        adv_form.addRow("FPS:", fps_row)

        layout.addWidget(self.advanced_panel)

        status_title = QLabel("Status do sistema")
        status_title.setObjectName("sectionTitle")
        layout.addWidget(status_title)

        self.latency_badge = QLabel("Latência: aguardando...")
        self.latency_badge.setObjectName("healthLabel")
        layout.addWidget(self.latency_badge)

        self.health_camera = QLabel()
        self.health_camera.setObjectName("healthLabel")
        self.health_obs = QLabel()
        self.health_obs.setObjectName("healthLabel")
        self.health_gestos = QLabel()
        self.health_gestos.setObjectName("healthLabel")

        layout.addWidget(self.health_camera)
        layout.addWidget(self.health_obs)
        layout.addWidget(self.health_gestos)

        layout.addStretch(1)

    def _on_advanced_toggle(self, checked):
        self.advanced_panel.setVisible(checked)
        self.advanced_toggle.setText(
            "Configurações Avançadas ▲" if checked else "Configurações Avançadas ▼"
        )

    def set_max_maos(self, max_maos):
        with vinculo.sem_sinais(self.maos_1_button, self.maos_2_button):
            if int(max_maos) == 2:
                self.maos_2_button.setChecked(True)
            else:
                self.maos_1_button.setChecked(True)

    AJUDA_POR_MODO = {
        "teste": "Detecta gestos sem executar nada — para calibrar.",
        "manual": "Conecta ao OBS e executa as ações. Sem câmera virtual.",
        "automatico": "Conecta ao OBS, executa as ações e liga a câmera virtual.",
    }

    def set_mode(self, modo):
        modo_norm = str(modo).lower()
        botoes = (self.mode_test_button, self.mode_manual_button, self.mode_auto_button)
        with vinculo.sem_sinais(*botoes):
            if modo_norm == "automatico":
                self.mode_auto_button.setChecked(True)
            elif modo_norm == "manual":
                self.mode_manual_button.setChecked(True)
            else:
                modo_norm = "teste"
                self.mode_test_button.setChecked(True)

        self.mode_help_label.setText(self.AJUDA_POR_MODO[modo_norm])

    def set_esqueleto(self, no_preview, na_saida_obs):
        botoes = (self.esqueleto_preview_button, self.esqueleto_obs_button)
        with vinculo.sem_sinais(*botoes):
            self.esqueleto_preview_button.setChecked(bool(no_preview))
            self.esqueleto_obs_button.setChecked(bool(na_saida_obs))

    def set_resolution(self, resolution_label):
        with vinculo.sem_sinais(*self.resolution_buttons.values()):
            alvo = self.resolution_buttons.get(resolution_label)
            (alvo or self.resolution_buttons["720p"]).setChecked(True)

    def set_fps(self, fps_value):
        with vinculo.sem_sinais(*self.fps_buttons.values()):
            alvo = self.fps_buttons.get(fps_value)
            (alvo or self.fps_buttons[30]).setChecked(True)

    def update_latency_badge(self, ms):
        if ms <= 33:
            color = "#4CAF50"
            status = "Ótima"
        elif ms <= 66:
            color = "#FFC107"
            status = "Boa"
        else:
            color = "#f44336"
            status = "Lenta"
        self.latency_badge.setText(f"⚡ Latência de processamento: {ms:.0f}ms — {status}")
        self.latency_badge.setStyleSheet(f"color: {color};")

    def reset_latency_badge(self):
        self.latency_badge.setText("Latência: aguardando...")
        self.latency_badge.setStyleSheet("")
