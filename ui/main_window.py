import cv2
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QMainWindow

from core.estado_app import EstadoApp
from ui.mixins.config_mixin import ConfigMixin
from ui.mixins.camera_mixin import CameraMixin
from ui.mixins.gesture_mixin import GestureMixin
from ui.mixins.obs_mixin import OBSMixin
from ui.mixins.engine_mixin import EngineMixin
from ui.mixins.health_mixin import HealthMixin
from ui.mixins.setup_mixin import SetupMixin
from util.caminhos import caminho_do_config
from util.logger import get_logger


logger = get_logger(__name__)


class MainWindow(QMainWindow, ConfigMixin, CameraMixin, GestureMixin, OBSMixin, EngineMixin, HealthMixin, SetupMixin):
    ALL_GESTURES = [
        ("V", "assets/icons/v_icon.png"),
        ("Joinha", "assets/icons/joinha_icon.png"),
        ("Mão aberta", "assets/icons/mao_aberta_icon.png"),
        ("Punho", "assets/icons/punho_icon.png"),
        ("Apontando p/ cima", "assets/icons/apontando_cima_icon.png"),
        ("Rock", "assets/icons/rock_icon.png"),
        ("Três", "assets/icons/tres_icon.png"),
        ("Quatro", "assets/icons/quatro_icon.png"),
        ("OK", "assets/icons/ok_icon.png"),
        ("Me liga", "assets/icons/me_liga_icon.png"),
        ("Deslike", "assets/icons/deslike_icon.png"),
        ("Dedo do Meio", "assets/icons/middle_finger.png"),
    ]

    def __init__(self, config, config_path=None):
        super().__init__()

        self.setWindowTitle("OBS GestureNode")
        self.setMinimumSize(1200, 760)

        # Sem config_path explícito, resolve pelo mesmo critério do main.py: ao lado do
        # código em desenvolvimento, %APPDATA% quando empacotado. Ver D-29.
        self._config_path = (
            Path(config_path) if config_path is not None else caminho_do_config()
        )

        # O estado é a fonte da verdade; a janela só reflete. Ver D-47.
        self.estado = EstadoApp(config, [nome for nome, _ in self.ALL_GESTURES])
        # Uma assinatura, no boot, no lugar das 14 chamadas manuais de save que existiam
        # espalhadas — e que só salvavam onde alguém tinha lembrado de pedir.
        self.estado.escutar(self._ao_mudar_estado)
        self.engine = None
        self._obs_connect_thread = None
        self.current_gesture = self.ALL_GESTURES[0][0]
        self._updating_gesture_form = False
        self.gesture_buttons = {}

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save_config)

        self._init_saude()
        self._setup_ui()
        self._load_ui_from_config()
        self.salvar_config_automatico()

        self._append_log("Interface inicializada")

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            engine_ativo = self.engine and self.engine.isRunning()
            modo_automatico = self.estado.modo == "automatico"
            if engine_ativo and modo_automatico:
                self.engine.set_preview_suprimido(self.isMinimized())
        super().changeEvent(event)

    def closeEvent(self, event):
        if self._obs_connect_thread is not None:
            try:
                self._obs_connect_thread.connected.disconnect()
                self._obs_connect_thread.failed.disconnect()
                self._obs_connect_thread.connecting.disconnect()
            except Exception:
                pass
            self._obs_connect_thread.wait(3000)
            self._obs_connect_thread = None

        if self.engine and self.engine.isRunning():
            # Único lugar onde bloquear é correto: destruir uma QThread ainda em execução
            # derruba o processo. Em todo o resto do app o `stop()` é assíncrono e quem
            # dirige a UI é o sinal `finished`. Ver D-34.
            self.engine.stop(esperar_ms=8000)

        super().closeEvent(event)

    def set_config_enabled(self, enabled):
        self.geral_tab.definir_controles_habilitados(enabled)

    def update_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        q_img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.preview_label.setPixmap(
            QPixmap.fromImage(q_img).scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def _clear_preview(self):
        self.preview_label.clear()
        self.preview_label.setText("Preview")

    @property
    def config(self):
        """O dicionário cru, para quem ainda precisa dele (engine, save, onboarding).

        **Só leitura.** Escrever aqui não notifica ninguém e a alteração não é salva —
        use as propriedades de `self.estado`.
        """
        return self.estado.config_bruta()

    def update_status(self, text):
        self.status_label.setText(text)
        self._append_log(text)
        if text == "OBS conectado":
            self.obs_footer_label.setText("🟢 OBS: Conectado")
        elif text.startswith("OBS:"):
            self.obs_footer_label.setText(self._resumir_footer_obs(text[len("OBS:"):].strip()))

    def _append_log(self, message):
        if not message:
            return
        self.log_view.appendPlainText(message)
