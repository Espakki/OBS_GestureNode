import cv2
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QMainWindow

from ui.mixins.config_mixin import ConfigMixin
from ui.mixins.camera_mixin import CameraMixin
from ui.mixins.gesture_mixin import GestureMixin
from ui.mixins.obs_mixin import OBSMixin
from ui.mixins.engine_mixin import EngineMixin
from ui.mixins.health_mixin import HealthMixin
from ui.mixins.setup_mixin import SetupMixin
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

        self.config = config or {}
        self._config_path = (
            Path(config_path)
            if config_path is not None
            else (Path(__file__).resolve().parent.parent / "config.json")
        )
        self.engine = None
        self._obs_connect_thread = None
        self.current_gesture = self.ALL_GESTURES[0][0]
        self._updating_gesture_form = False
        self.gesture_buttons = {}

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save_config)

        self._init_config_schema()
        self._setup_ui()
        self._load_ui_from_config()
        self.salvar_config_automatico()

        self._append_log("Interface inicializada")

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            engine_ativo = self.engine and self.engine.isRunning()
            modo_automatico = self.config.get("modo") == "automatico"
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
            self.engine.stop()

        super().closeEvent(event)

    def set_config_enabled(self, enabled):
        self.camera_device_combo.setEnabled(enabled)
        for button in self.resolution_buttons.values():
            button.setEnabled(enabled)
        for button in self.fps_buttons.values():
            button.setEnabled(enabled)

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

    def update_status(self, text):
        self.status_label.setText(text)
        self._append_log(text)
        self._update_runtime_health_from_status(text)
        if text == "OBS conectado":
            self.obs_footer_label.setText("🟢 OBS: Conectado")
        elif text.startswith("OBS:"):
            self.obs_footer_label.setText(self._resumir_footer_obs(text[len("OBS:"):].strip()))

    def _append_log(self, message):
        if not message:
            return
        self.log_view.appendPlainText(message)
