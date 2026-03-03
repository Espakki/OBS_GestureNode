from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget


class OBSTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Conexão OBS")
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(14)
        layout.addLayout(form)

        self.obs_host = QLineEdit()
        form.addRow("Host:", self.obs_host)

        self.obs_port = QSpinBox()
        self.obs_port.setRange(1, 99999)
        form.addRow("Porta:", self.obs_port)

        self.obs_password = QLineEdit()
        self.obs_password.setEchoMode(QLineEdit.Password)
        form.addRow("Password:", self.obs_password)

        self.test_obs_button = QPushButton("Testar conexão")
        layout.addWidget(self.test_obs_button)

        self.obs_status_label = QLabel("Status: Desconectado")
        layout.addWidget(self.obs_status_label)

        layout.addStretch(1)
