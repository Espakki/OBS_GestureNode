from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget

from core.estado_runtime import EstadoOBS

TEXTO_PADRAO = {
    EstadoOBS.CONECTADO: "Conectado",
    EstadoOBS.CONECTANDO: "Conectando...",
    EstadoOBS.FALHOU: "Falha de conexão",
    EstadoOBS.DESATIVADO: "Desativado (modo Teste)",
    EstadoOBS.NAO_TESTADO: "Desconectado",
}


class OBSTab(QWidget):
    """A aba OBS em Qt Widgets. Mesmo contrato da versão QML."""

    testePedido = Signal()
    credenciaisMudaram = Signal()

    def __init__(self, estado=None):
        super().__init__()
        self._estado = estado

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        title = QLabel("Conexão OBS")
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addLayout(form)

        self.obs_host = QLineEdit()
        self.obs_host.setPlaceholderText("Ex: localhost")
        self.obs_host.setToolTip("Host do OBS WebSocket. Em geral use localhost quando o OBS está no mesmo PC.")
        form.addRow("Host:", self.obs_host)

        self.obs_port = QSpinBox()
        self.obs_port.setRange(1, 99999)
        self.obs_port.setValue(4455)
        self.obs_port.setToolTip("Porta do OBS WebSocket. O padrão atual do OBS é 4455.")
        form.addRow("Porta:", self.obs_port)

        self.obs_password = QLineEdit()
        self.obs_password.setEchoMode(QLineEdit.Password)
        self.obs_password.setPlaceholderText("Senha do OBS WebSocket")
        self.obs_password.setToolTip("Senha definida nas configurações do servidor WebSocket no OBS.")
        form.addRow("Senha:", self.obs_password)

        self.test_obs_button = QPushButton("Testar conexão")
        self.test_obs_button.setMinimumHeight(38)
        self.test_obs_button.setToolTip("Verifica se host, porta e senha conseguem conectar ao OBS.")
        layout.addWidget(self.test_obs_button)

        self.obs_status_label = QLabel("Status: Desconectado")
        layout.addWidget(self.obs_status_label)

        self.obs_help_label = QLabel(
            "Conecte o controlador ao OBS para controlar suas cenas e fontes usando gestos. Certifique-se de que o plugin OBS WebSocket esteja instalado e configurado corretamente."
        )
        self.obs_help_label.setObjectName("muted")
        self.obs_help_label.setWordWrap(True)
        layout.addWidget(self.obs_help_label)

        self.obs_plugin_link_label = QLabel(
            "Download OBS WebSocket: "
            "<a href='https://github.com/obsproject/obs-websocket/releases'>"
            "github.com/obsproject/obs-websocket/releases"
            "</a>"
        )
        self.obs_plugin_link_label.setObjectName("muted")
        self.obs_plugin_link_label.setWordWrap(True)
        self.obs_plugin_link_label.setOpenExternalLinks(True)
        self.obs_plugin_link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.obs_plugin_link_label.setToolTip("Clique para abrir a página oficial de releases do OBS WebSocket.")
        layout.addWidget(self.obs_plugin_link_label)

        layout.addStretch(1)

        self.test_obs_button.clicked.connect(self.testePedido.emit)
        for campo in (self.obs_host, self.obs_password):
            campo.textEdited.connect(self._ao_editar)
        self.obs_port.valueChanged.connect(self._ao_editar)

    def _ao_editar(self, *_):
        if self._estado is not None:
            self._estado.obs_host = self.obs_host.text().strip()
            self._estado.obs_porta = int(self.obs_port.value())
            self._estado.obs_senha = self.obs_password.text()
        self.credenciaisMudaram.emit()

    def definir_status(self, situacao, detalhe=""):
        self.obs_status_label.setText(detalhe or TEXTO_PADRAO.get(situacao, "Desconectado"))
        self.test_obs_button.setEnabled(situacao is not EstadoOBS.CONECTANDO)

    def texto_do_status(self):
        return self.obs_status_label.text()

    def definir_controles_habilitados(self, ligado):
        """A aba OBS não trava com a engine rodando."""
