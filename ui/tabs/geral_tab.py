from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


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

        title = QLabel("Configurações Gerais")
        title.setObjectName("title")
        layout.addWidget(title)

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
        self.mode_obs_button = QPushButton("OBS")
        for button in (self.mode_test_button, self.mode_obs_button):
            button.setObjectName("optionToggle")
            button.setCheckable(True)
            button.setMinimumWidth(92)
            button.setMinimumHeight(38)
            mode_layout.addWidget(button)
            self.mode_group.addButton(button)
        form.addRow("Modo:", mode_row)

        self.mode_test_button.setToolTip(
            "Modo Teste: use para calibrar gestos, câmera e ações sem enviar comandos para o OBS."
        )
        self.mode_obs_button.setToolTip(
            "Modo OBS: use na live para enviar ações ao OBS e usar câmera virtual quando habilitada."
        )

        self.mode_help_label = QLabel(
            "Modo Teste: ideal para configurar e validar seus gestos com segurança.\n"
            "Modo OBS: ativa integração ao OBS para executar ações e operar com câmera virtual."
        )
        self.mode_help_label.setObjectName("muted")
        self.mode_help_label.setWordWrap(True)
        layout.addWidget(self.mode_help_label)

        self.show_skeleton_checkbox = QCheckBox("Mostrar esqueleto da mão no preview")
        self.show_skeleton_checkbox.setToolTip(
            "Exibe o esqueleto da mão no preview para facilitar o ajuste de posição e iluminação."
        )
        layout.addWidget(self.show_skeleton_checkbox)

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
        camera_form.addRow("Resolução:", resolution_row)

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
        camera_form.addRow("FPS:", fps_row)

        status_title = QLabel("Status do sistema")
        status_title.setObjectName("sectionTitle")
        layout.addWidget(status_title)

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

    def set_mode(self, modo):
        if str(modo).lower() == "obs":
            self.mode_obs_button.setChecked(True)
        else:
            self.mode_test_button.setChecked(True)

    def set_resolution(self, resolution_label):
        target = self.resolution_buttons.get(resolution_label)
        if target:
            target.setChecked(True)
            return
        self.resolution_buttons["720p"].setChecked(True)

    def set_fps(self, fps_value):
        if fps_value in self.fps_buttons:
            self.fps_buttons[fps_value].setChecked(True)
            return
        self.fps_buttons[30].setChecked(True)
