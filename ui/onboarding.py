from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

_STEPS = [
    (
        "1/4 — Câmera",
        (
            "Selecione sua câmera na aba <b>Geral → Dispositivo</b>.<br><br>"
            "Em <b>Configurações Avançadas</b> você pode ajustar resolução, FPS e o modo "
            "da câmera virtual.<br><br>"
            "O modo <b>Automático</b> (recomendado) detecta o device de câmera virtual sem "
            "configuração manual. Use o modo <b>Manual</b> apenas se houver conflito de driver.<br><br>"
            "O app usa a câmera exclusivamente para detectar gestos — nenhuma imagem é gravada "
            "ou enviada para qualquer servidor."
        ),
    ),
    (
        "2/4 — Modo de Operação",
        (
            "<b>Teste</b>: a câmera roda e os gestos aparecem no preview, mas nenhuma ação "
            "é executada. Use para calibrar posição, iluminação e tempo de resposta antes de "
            "usar ao vivo.<br><br>"
            "<b>Manual</b>: conecta ao OBS via WebSocket e executa as ações configuradas "
            "(trocar cena, atalhos, áudio). A câmera virtual fica desativada — ideal se "
            "houver conflito de driver.<br><br>"
            "<b>Automático</b>: igual ao Manual, mas também gerencia a câmera virtual "
            "automaticamente. Certifique-se de fechar o OBS antes de iniciar o app, depois "
            "abra o OBS e adicione <i>OBS Virtual Camera</i> como fonte de captura."
        ),
    ),
    (
        "3/4 — OBS Studio",
        (
            "Para usar nos modos <b>Manual</b> ou <b>Automático</b>:<br><br>"
            "1. Abra o OBS Studio.<br>"
            "2. Vá em <b>Ferramentas → Configurações do servidor WebSocket</b> e "
            "ative o servidor.<br>"
            "3. Na aba <b>OBS</b> deste app, preencha host (padrão: <i>localhost</i>), "
            "porta (padrão: <i>4455</i>) e senha (se configurada).<br>"
            "4. Clique em <b>Testar conexão</b> para verificar.<br><br>"
            "No modo <b>Automático</b>, para que o feed da câmera apareça no OBS, adicione "
            "a fonte <i>OBS Virtual Camera</i> em uma cena no OBS após iniciar o app."
        ),
    ),
    (
        "4/4 — Primeiro Gesto",
        (
            "Na aba <b>Gestos</b>:<br><br>"
            "1. Clique em <b>Selecionar gestos ativos</b> e ative o gesto desejado.<br>"
            "2. Selecione o gesto na grade e configure a ação (cena, atalho ou som).<br>"
            "3. Ajuste o <b>Tempo de resposta</b> — recomendamos <b>2.0s</b> para evitar "
            "disparos acidentais durante a fala.<br>"
            "4. Clique em <b>Iniciar</b> na parte inferior e faça o gesto diante da câmera.<br><br>"
            "<b>Dica:</b> comece sempre no modo <b>Teste</b> até confirmar que o gesto é "
            "detectado corretamente antes de usar ao vivo."
        ),
    ),
]


class OnboardingDialog(QDialog):
    def __init__(self, config, save_callback, parent=None):
        super().__init__(parent)
        self._config = config
        self._save_callback = save_callback

        self.setWindowTitle("Bem-vindo ao OBS GestureNode")
        self.setMinimumWidth(540)
        self.setMinimumHeight(360)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self._stack = QStackedWidget()
        for step_title, step_content in _STEPS:
            self._stack.addWidget(self._make_page(step_title, step_content))
        layout.addWidget(self._stack, stretch=1)

        nav = QHBoxLayout()
        self._back_btn = QPushButton("Anterior")
        self._next_btn = QPushButton("Próximo")
        self._next_btn.setDefault(True)
        self._next_btn.setMinimumWidth(100)
        nav.addWidget(self._back_btn)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        self._back_btn.clicked.connect(self._go_back)
        self._next_btn.clicked.connect(self._go_next)
        self._update_nav()

    def _make_page(self, title, content):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        page_layout.addWidget(title_label)

        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.RichText)
        content_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_label.setOpenExternalLinks(False)
        page_layout.addWidget(content_label, stretch=1)
        return page

    def _go_back(self):
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
        self._update_nav()

    def _go_next(self):
        idx = self._stack.currentIndex()
        if idx < self._stack.count() - 1:
            self._stack.setCurrentIndex(idx + 1)
            self._update_nav()
        else:
            self._finish()

    def _update_nav(self):
        idx = self._stack.currentIndex()
        self._back_btn.setEnabled(idx > 0)
        self._next_btn.setText("Concluir" if idx == self._stack.count() - 1 else "Próximo")

    def _finish(self):
        self._config["onboarding_done"] = True
        self._save_callback()
        self.accept()

    def closeEvent(self, event):
        self._config["onboarding_done"] = True
        self._save_callback()
        super().closeEvent(event)
