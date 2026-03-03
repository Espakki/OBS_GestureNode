from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget


class GeralTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Configurações Gerais")
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(14)
        layout.addLayout(form)

        self.modo_combo = QComboBox()
        self.modo_combo.addItems(["test", "obs"])
        form.addRow("Modo:", self.modo_combo)

        self.show_skeleton_checkbox = QCheckBox("Mostrar esqueleto da mão no preview")
        layout.addWidget(self.show_skeleton_checkbox)

        status_title = QLabel("Saúde do sistema")
        status_title.setObjectName("title")
        layout.addWidget(status_title)

        self.health_camera = QLabel()
        self.health_obs = QLabel()
        self.health_gestos = QLabel()

        layout.addWidget(self.health_camera)
        layout.addWidget(self.health_obs)
        layout.addWidget(self.health_gestos)

        layout.addStretch(1)
