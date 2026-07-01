import json
import os
import tempfile
from pathlib import Path
import cv2

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtMultimedia import QMediaDevices
except Exception:  # pragma: no cover - fallback quando QtMultimedia não estiver disponível
    QMediaDevices = None

try:
    from pygrabber.dshow_graph import FilterGraph  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - pygrabber é opcional
    FilterGraph = None

from core.gesture_aliases import GESTURE_ALIASES
from engine.gesture_engine import GestureEngine
from integrations.obs_connect_thread import _resumir_footer_obs as _resumir_footer_obs_fn
from ui.tabs.geral_tab import GeralTab
from ui.tabs.gestos_tab import GestosTab
from ui.tabs.obs_tab import OBSTab
from util.logger import get_logger


logger = get_logger(__name__)


RESOLUTION_PRESETS = {
    "480p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}

RESOLUTION_PRESETS_REVERSED = {
    value: key
    for key, value in RESOLUTION_PRESETS.items()
}


class MainWindow(QMainWindow):
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
        ("Arminha", "assets/icons/pistol.png"),
        ("Escoteiro", "assets/icons/scout.png"),
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

    def _init_config_schema(self):
        self.config.setdefault("modo", "test")

        camera_cfg = self.config.setdefault("camera", {})
        camera_cfg.setdefault("index", 0)
        camera_cfg.setdefault("device_name", "")
        camera_cfg.setdefault("width", 1280)
        camera_cfg.setdefault("height", 720)
        camera_cfg.setdefault("fps", 30)
        camera_cfg.setdefault("process_fps", 30)
        camera_cfg.setdefault("enable_virtual_camera", False)
        camera_cfg.setdefault("virtual_camera_device", None)
        camera_cfg.setdefault("show_skeleton", True)

        obs_cfg = self.config.setdefault("obs", {})
        obs_cfg.setdefault("host", "localhost")
        obs_cfg.setdefault("port", 4455)
        obs_cfg.setdefault("password", "")

        gestures_cfg = self.config.setdefault("gestures", {})
        default_hold = gestures_cfg.get("default_hold_time", gestures_cfg.get("hold_time", 2.0))
        default_cooldown = gestures_cfg.get("default_cooldown", gestures_cfg.get("cooldown", 2.0))
        # Garantir mínimo de 0.5s para hold_time (2.0s é o recomendado)
        # e 2.0 segundos para cooldown
        default_hold = max(0.5, float(default_hold))
        default_cooldown = max(2.0, float(default_cooldown))
        gestures_cfg["default_hold_time"] = default_hold
        gestures_cfg["default_cooldown"] = default_cooldown

        raw_scene_map = gestures_cfg.get("scene_map", {}) or {}
        raw_bindings = gestures_cfg.get("bindings", {}) or {}

        scene_map = {
            GESTURE_ALIASES.get(key, key): value
            for key, value in raw_scene_map.items()
        }
        bindings = {
            GESTURE_ALIASES.get(key, key): value
            for key, value in raw_bindings.items()
        }

        normalized = {}
        gesture_ids = [gesture for gesture, _ in self.ALL_GESTURES]

        active_gestures = gestures_cfg.get("active_gestures")
        if not isinstance(active_gestures, list) or not active_gestures:
            active_gestures = [
                gesture
                for gesture, cfg in bindings.items()
                if isinstance(cfg, dict) and cfg.get("enabled", True)
            ]
        if not active_gestures:
            active_gestures = [gesture_ids[0]]

        gestures_cfg["active_gestures"] = [
            gesture
            for gesture in active_gestures
            if gesture in gesture_ids
        ]
        if not gestures_cfg["active_gestures"]:
            gestures_cfg["active_gestures"] = [gesture_ids[0]]

        for gesture, _ in self.ALL_GESTURES:
            raw = bindings.get(gesture, {}) if isinstance(bindings, dict) else {}
            hold_time = float(raw.get("hold_time", gestures_cfg["default_hold_time"]))
            cooldown = float(raw.get("cooldown", gestures_cfg["default_cooldown"]))
            # Garantir mínimos: hold_time >= 0.5s, cooldown >= 2.0s
            hold_time = max(0.5, hold_time)
            cooldown = max(2.0, cooldown)
            normalized[gesture] = {
                "enabled": bool(raw.get("enabled", gesture in gestures_cfg["active_gestures"])),
                "hold_time": hold_time,
                "cooldown": cooldown,
                "scene": str(raw.get("scene", scene_map.get(gesture, ""))).strip(),
                "play_sound": bool(raw.get("play_sound", False)),
                "sound_file": str(raw.get("sound_file", "")).strip(),
                "hotkey": str(raw.get("hotkey", "")).strip(),
                "use_scene": bool(raw.get("use_scene", bool(raw.get("scene", scene_map.get(gesture, ""))))),
                "use_sound": bool(raw.get("use_sound", bool(raw.get("play_sound", False)))),
                "use_hotkey": bool(raw.get("use_hotkey", bool(raw.get("hotkey", "")))),
            }

        gestures_cfg["bindings"] = normalized
        self._sync_scene_map_from_bindings()

    @staticmethod
    def _is_virtual_camera_name(name):
        value = (name or "").strip().lower()
        virtual_tokens = (
            "obs virtual",
            "virtual camera",
            "vcam",
            "xsplit",
            "manycam",
            "snap camera",
        )
        return any(token in value for token in virtual_tokens)

    def _normalize_camera_display_name(self, name, index):
        clean_name = (name or "").strip()
        if self._is_virtual_camera_name(clean_name):
            return "OBS Virtual Camera"
        if clean_name:
            return clean_name
        return f"Câmera {index}"

    @staticmethod
    def _probe_opencv_camera_indexes(max_devices=10):
        import sys
        from io import StringIO
        
        available_indexes = []
        
        # Suprimir avisos de OpenCV durante probing (compatível com todas as versões)
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            for index in range(max_devices):
                capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if not capture or not capture.isOpened():
                    if capture:
                        capture.release()
                    continue

                ok, _ = capture.read()
                capture.release()
                if ok:
                    available_indexes.append(index)
        finally:
            # Restaurar stderr original
            sys.stderr = old_stderr

        return available_indexes

    @staticmethod
    def _dshow_device_names():
        if FilterGraph is None:
            return []

        try:
            graph = FilterGraph()
            return list(graph.get_input_devices() or [])
        except Exception as exc:
            logger.debug("Falha ao listar dispositivos DirectShow: %s", exc)
            return []

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #111418; color: #E6E6E6; font-size: 15px; }
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QTabWidget::pane { border: 1px solid #2a2f36; background: #1a1f26; }
            QTabBar::tab { background: #222831; min-width: 92px; padding: 10px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-size: 15px; }
            QTabBar::tab:selected { background: #2d3642; color: #ffcc33; }
            QFrame#card { background: #1a1f26; border: 1px solid #2a2f36; border-radius: 10px; }
            QFrame#bottomPanel { background: #1a1f26; border: 1px solid #2a2f36; border-radius: 8px; }
            QWidget#transparentRow { background: transparent; }
            QLabel { font-size: 15px; background: transparent; }
            QLabel#sectionTitle { color: #d9dee7; font-size: 17px; font-weight: 700; background: transparent; }
            QLabel#muted { color: #9aa4b2; font-size: 14px; background: transparent; }
            QLabel#healthLabel { color: #cfd8e3; font-size: 14px; background: transparent; }
            QCheckBox { spacing: 8px; font-size: 15px; background: transparent; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QRadioButton { spacing: 8px; font-size: 15px; background: transparent; }
            QLabel#title { color: #ffcc33; font-size: 22px; font-weight: 800; background: transparent; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QSlider {
                background: #252b33;
                border: 1px solid #3b4654;
                border-radius: 6px;
                padding: 8px;
                margin-bottom: 5px;
                color: #f1f1f1;
                min-height: 20px;
            }
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
                background: #1b2029;
                border: 1px solid #2f3642;
                color: #7f8794;
            }
            QComboBox {
                background: #252b33;
                border: 1px solid #3b4654;
                border-radius: 6px;
                padding: 8px;
                margin-bottom: 5px;
                color: #f1f1f1;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #1f6feb;
            }
            QComboBox:disabled {
                background: #1b2029;
                border: 1px solid #2f3642;
                color: #7f8794;
            }
            QPushButton, QToolButton { background: #1f6feb; border: none; border-radius: 8px; padding: 10px 14px; color: white; font-weight: 600; font-size: 15px; outline: none; }
            QPushButton:focus, QToolButton:focus { outline: none; }
            QPushButton:hover { background: #2c7dff; }
            QToolButton:hover { background: #2c7dff; }
            QPushButton:disabled, QToolButton:disabled {
                background: #263548;
                color: #7f95b0;
            }
            QPushButton#danger { background: #d63d3d; }
            QPushButton#warning { background: #d08a00; }
            QPushButton#ghost { background: #2a2f36; }
            QPushButton#optionToggle { background: #252b33; border: 1px solid #3a4655; }
            QPushButton#optionToggle:hover { background: #2b3341; border: 1px solid #4a5a6e; }
            QPushButton#optionToggle:pressed { background: #1e2530; border: 1px solid #6b7f99; }
            QPushButton#optionToggle:focus { border: 1px solid #3a4655; }
            QPushButton#optionToggle:checked { background: #1f6feb; border: 1px solid #1f6feb; color: #ffffff; }
            QPushButton#optionToggle:checked:hover { background: #2c7dff; border: 1px solid #2c7dff; }
            QPushButton#optionToggle:checked:pressed { background: #1761cf; border: 1px solid #1761cf; }
            QPushButton#gestureBtn, QToolButton#gestureBtn { background: #252b33; border: 1px solid #3a4655; padding: 15px; max-height: 150px; }
            QPushButton#gestureBtn:checked, QToolButton#gestureBtn:checked { border: 2px solid #ffcc33; background: #2f3742; }
            QPushButton#gestureSelect, QToolButton#gestureSelect {
                background: #252b33;
                border: 1px solid #3a4655;
                min-height: 64px;
                padding: 8px;
            }
            QPushButton#gestureSelect:hover, QToolButton#gestureSelect:hover { background: #2b3341; border: 1px solid #4a5a6e; }
            QPushButton#gestureSelect:pressed, QToolButton#gestureSelect:pressed { background: #1e2530; border: 1px solid #6b7f99; }
            QPushButton#gestureSelect:focus, QToolButton#gestureSelect:focus { border: 1px solid #3a4655; }
            QPushButton#gestureSelect:checked, QToolButton#gestureSelect:checked {
                border: 2px solid #ffcc33;
                background: #2f3742;
            }
            QPushButton#gestureSelect:checked:hover, QToolButton#gestureSelect:checked:hover {
                background: #364154;
            }
            QPushButton#gestureSelect:checked:pressed, QToolButton#gestureSelect:checked:pressed {
                background: #293244;
            }
            QFrame#card QPushButton { background: #1f6feb; color: white; border: none; }
            QFrame#card QPushButton#danger { background: #d63d3d; color: white; }
            QFrame#card QPushButton#warning { background: #d08a00; color: white; }
            QFrame#card QPushButton#ghost { background: #2a2f36; color: white; }
            QFrame#card QPushButton#optionToggle { background: #252b33; color: white; border: 1px solid #3a4655; }
            QFrame#card QPushButton#optionToggle:hover { background: #2b3341; border: 1px solid #4a5a6e; }
            QFrame#card QPushButton#optionToggle:pressed { background: #1e2530; border: 1px solid #6b7f99; }
            QFrame#card QPushButton#optionToggle:focus { border: 1px solid #3a4655; }
            QFrame#card QPushButton#optionToggle:checked { background: #1f6feb; color: white; border: 1px solid #1f6feb; }
            QFrame#card QPushButton#optionToggle:checked:hover { background: #2c7dff; border: 1px solid #2c7dff; }
            QFrame#card QPushButton#optionToggle:checked:pressed { background: #1761cf; border: 1px solid #1761cf; }
            QFrame#card QPushButton#gestureBtn, QFrame#card QToolButton#gestureBtn { background: #252b33; color: white; }
            QFrame#card QPushButton#gestureBtn:checked, QFrame#card QToolButton#gestureBtn:checked { background: #2f3742; color: #ffcc33; }
            QFrame#card QPushButton#gestureSelect, QFrame#card QToolButton#gestureSelect {
                background: #252b33;
                color: white;
                border: 1px solid #3a4655;
            }
            QFrame#card QPushButton#gestureSelect:hover, QFrame#card QToolButton#gestureSelect:hover {
                background: #2b3341;
                border: 1px solid #4a5a6e;
            }
            QFrame#card QPushButton#gestureSelect:pressed, QFrame#card QToolButton#gestureSelect:pressed {
                background: #1e2530;
                border: 1px solid #6b7f99;
            }
            QFrame#card QPushButton#gestureSelect:focus, QFrame#card QToolButton#gestureSelect:focus {
                border: 1px solid #3a4655;
            }
            QFrame#card QPushButton#gestureSelect:checked, QFrame#card QToolButton#gestureSelect:checked {
                background: #2f3742;
                color: #ffcc33;
                border: 2px solid #ffcc33;
            }
            QFrame#card QPushButton#gestureSelect:checked:hover, QFrame#card QToolButton#gestureSelect:checked:hover {
                background: #364154;
            }
            QFrame#card QPushButton#gestureSelect:checked:pressed, QFrame#card QToolButton#gestureSelect:checked:pressed {
                background: #293244;
            }
            QPlainTextEdit { background: #0f1318; border: 1px solid #2a2f36; border-radius: 8px; color: #d4dde8; }
            QSlider::groove:horizontal { height: 10px; background: #3a4049; border-radius: 5px; margin: 6px 0; }
            QSlider::handle:horizontal { background: #ffcc33; width: 20px; margin: -6px 0; border-radius: 10px; }
            """
        )

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

        self.geral_tab = GeralTab()
        self.gestos_tab = GestosTab()
        self.obs_tab = OBSTab()

        self.tabs.addTab(self.geral_tab, "Geral")
        self.tabs.addTab(self.gestos_tab, "Gestos")
        self.tabs.addTab(self.obs_tab, "OBS")

        self.mode_test_button = self.geral_tab.mode_test_button
        self.mode_obs_button = self.geral_tab.mode_obs_button
        self.show_skeleton_checkbox = self.geral_tab.show_skeleton_checkbox
        self.camera_device_combo = self.geral_tab.camera_device_combo
        self.resolution_buttons = self.geral_tab.resolution_buttons
        self.fps_buttons = self.geral_tab.fps_buttons
        self.health_camera = self.geral_tab.health_camera
        self.health_obs = self.geral_tab.health_obs
        self.health_gestos = self.geral_tab.health_gestos

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

        self.mode_test_button.toggled.connect(lambda checked: self.on_modo_changed("test") if checked else None)
        self.mode_obs_button.toggled.connect(lambda checked: self.on_modo_changed("obs") if checked else None)
        self.show_skeleton_checkbox.toggled.connect(self.on_show_skeleton_changed)
        self.show_skeleton_checkbox.toggled.connect(self.on_dynamic_setting_changed)
        self.camera_device_combo.currentIndexChanged.connect(self.on_camera_changed)
        for label, button in self.resolution_buttons.items():
            button.toggled.connect(lambda checked, value=label: self.on_resolution_changed(value) if checked else None)
        for fps_value, button in self.fps_buttons.items():
            button.toggled.connect(lambda checked, value=fps_value: self.on_fps_changed(value) if checked else None)

        self.choose_gestures_button.clicked.connect(self.open_gesture_selector_dialog)
        self.hold_slider.valueChanged.connect(self.on_hold_slider_changed)
        self.hold_slider.valueChanged.connect(self.on_current_gesture_changed)
        self.hold_slider.valueChanged.connect(self.on_dynamic_setting_changed)
        self.hold_value_spinbox.valueChanged.connect(self.on_hold_spinbox_changed)
        self.hold_value_spinbox.valueChanged.connect(self.on_current_gesture_changed)
        self.hold_value_spinbox.valueChanged.connect(self.on_dynamic_setting_changed)
        
        self.cooldown_slider.valueChanged.connect(self.on_cooldown_slider_changed)
        self.cooldown_slider.valueChanged.connect(self.on_current_gesture_changed)
        self.cooldown_slider.valueChanged.connect(self.on_dynamic_setting_changed)
        self.cooldown_value_spinbox.valueChanged.connect(self.on_cooldown_spinbox_changed)
        self.cooldown_value_spinbox.valueChanged.connect(self.on_current_gesture_changed)
        self.cooldown_value_spinbox.valueChanged.connect(self.on_dynamic_setting_changed)
        
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
        self.preview_label.setStyleSheet("background-color: #0f1318; border: 1px solid #2a2f36; border-radius: 8px;")
        right_layout.addWidget(self.preview_label, stretch=1)

        bottom_panel = QFrame()
        bottom_panel.setObjectName("bottomPanel")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(8)

        controls_layout = QHBoxLayout()
        bottom_layout.addLayout(controls_layout)

        self.start_button = QPushButton("Iniciar")
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

    def _active_gestures(self):
        gesture_ids = {gesture for gesture, _ in self.ALL_GESTURES}
        configured = self.config.setdefault("gestures", {}).setdefault("active_gestures", [])
        valid = [gesture for gesture in configured if gesture in gesture_ids]
        if not valid:
            valid = [self.ALL_GESTURES[0][0]]
        self.config["gestures"]["active_gestures"] = valid
        return valid

    def _rebuild_gesture_grid(self):
        self.gestos_tab.clear_gesture_grid()

        self.gesture_buttons = {}
        active = set(self._active_gestures())
        visible_gestures = [item for item in self.ALL_GESTURES if item[0] in active]

        for idx, (gesture, icon_path) in enumerate(visible_gestures):
            row = idx // 4
            col = idx % 4
            callback = lambda _=None, g=gesture: self.select_gesture(g)
            btn = self.gestos_tab.add_gesture_button(row, col, gesture, callback)
            self._configure_gesture_button(btn, gesture, icon_path)
            self.gesture_buttons[gesture] = btn

        if self.current_gesture not in self.gesture_buttons and self.gesture_buttons:
            self.current_gesture = next(iter(self.gesture_buttons.keys()))

        if self.gesture_buttons:
            self.select_gesture(self.current_gesture)

    def _populate_camera_devices(self):
        self.camera_device_combo.blockSignals(True)
        self.camera_device_combo.clear()

        camera_cfg = self.config.setdefault("camera", {})
        selected_index = int(camera_cfg.get("index", 0))
        selected_name = str(camera_cfg.get("device_name", "") or "").strip()

        available_indexes = self._probe_opencv_camera_indexes()
        if not available_indexes:
            available_indexes = [0]

        dshow_names = self._dshow_device_names()
        qt_names = []
        if QMediaDevices is not None:
            try:
                qt_names = [device.description() for device in QMediaDevices.videoInputs()]
            except Exception as exc:
                logger.debug("Falha ao listar dispositivos de vídeo no Qt: %s", exc)

        camera_entries = []
        for index in available_indexes:
            name = ""
            if index < len(dshow_names):
                name = dshow_names[index]
            elif index < len(qt_names):
                name = qt_names[index]
            name = self._normalize_camera_display_name(name, index)

            camera_entries.append((name, index))

        # Mantém câmeras físicas primeiro para evitar seleção acidental da virtual no primeiro uso.
        camera_entries.sort(key=lambda item: (self._is_virtual_camera_name(item[0]), item[1]))

        for name, index in camera_entries:
            self.camera_device_combo.addItem(name, index)

        selected_pos = 0
        for pos in range(self.camera_device_combo.count()):
            if int(self.camera_device_combo.itemData(pos)) == selected_index:
                selected_pos = pos
                break
        else:
            if selected_name:
                for pos in range(self.camera_device_combo.count()):
                    if self.camera_device_combo.itemText(pos).strip().lower() == selected_name.lower():
                        selected_pos = pos
                        break
                else:
                    for pos in range(self.camera_device_combo.count()):
                        if not self._is_virtual_camera_name(self.camera_device_combo.itemText(pos)):
                            selected_pos = pos
                            break
            else:
                for pos in range(self.camera_device_combo.count()):
                    if not self._is_virtual_camera_name(self.camera_device_combo.itemText(pos)):
                        selected_pos = pos
                        break

        self.camera_device_combo.setCurrentIndex(selected_pos)
        selected_data = self.camera_device_combo.currentData()
        if selected_data is not None:
            camera_cfg["index"] = int(selected_data)
        camera_cfg["device_name"] = self.camera_device_combo.currentText().strip()
        self.camera_device_combo.blockSignals(False)

    def _resolve_asset_path(self, icon_path):
        if not icon_path:
            return ""
        if os.path.isabs(icon_path):
            return icon_path
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", icon_path))

    def _configure_gesture_button(self, button, gesture_name, icon_path):
        button.setMinimumSize(110, 140)
        button.setIconSize(QSize(64, 64))

        formatted_text = self._format_selector_label(gesture_name)
        resolved_icon = self._resolve_asset_path(icon_path)
        if resolved_icon and os.path.exists(resolved_icon):
            button.setIcon(QIcon(resolved_icon))
        else:
            button.setIcon(QIcon())

        button.setText(formatted_text)
        button.setProperty("emojiText", formatted_text)
        button.setProperty("fullText", formatted_text)

    def _format_selector_label(self, gesture_name):
        if gesture_name == "Apontando p/ cima":
            return "Apontando\np/ cima"
        if gesture_name == "Mão aberta":
            return "Mão\naberta"
        if gesture_name == "Dedo do Meio":
            return "Dedo\ndo Meio"
        return gesture_name

    def open_gesture_selector_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Escolher gestos ativos")
        dialog.resize(450, 720)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.addWidget(QLabel("Selecione os gestos ativos para a tela principal:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        content_layout.addLayout(grid)

        active_set = set(self._active_gestures())
        gesture_buttons = {}
        for gesture, icon_path in self.ALL_GESTURES:
            button = QToolButton()
            button.setText(self._format_selector_label(gesture))
            button.setObjectName("gestureSelect")
            button.setCheckable(True)
            button.setChecked(gesture in active_set)
            button.setFixedSize(110, 110)
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            resolved_icon = self._resolve_asset_path(icon_path)
            if resolved_icon and os.path.exists(resolved_icon):
                button.setIcon(QIcon(resolved_icon))
                button.setIconSize(QSize(36, 36))
            else:
                button.setIconSize(QSize(0, 0))
            row = len(gesture_buttons) // 3
            col = len(gesture_buttons) % 3
            grid.addWidget(button, row, col)
            gesture_buttons[gesture] = button

        for col in range(3):
            grid.setColumnStretch(col, 1)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        dialog_layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_layout.addWidget(buttons)

        def on_accept():
            selected = [gesture for gesture, button in gesture_buttons.items() if button.isChecked()]
            if not selected:
                QMessageBox.warning(dialog, "Seleção inválida", "Selecione pelo menos um gesto.")
                return

            self.config.setdefault("gestures", {})["active_gestures"] = selected
            bindings = self.config.setdefault("gestures", {}).setdefault("bindings", {})
            for gesture, cfg in bindings.items():
                if isinstance(cfg, dict):
                    cfg["enabled"] = gesture in selected

            # Atualiza o engine em tempo real se estiver rodando
            if self.engine and self.engine.isRunning():
                gestures_cfg = self.config.get("gestures", {})
                self.engine.gesture_bindings = gestures_cfg.get("bindings", {})

            self._rebuild_gesture_grid()
            self._refresh_health_panels()
            self.salvar_config_automatico()
            dialog.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

    def _load_ui_from_config(self):
        camera_cfg = self.config.get("camera", {})
        obs_cfg = self.config.get("obs", {})

        self.geral_tab.set_mode(self.config.get("modo", "test"))

        self._populate_camera_devices()
        width = int(camera_cfg.get("width", 1280))
        height = int(camera_cfg.get("height", 720))
        self.geral_tab.set_resolution(RESOLUTION_PRESETS_REVERSED.get((width, height), "720p"))
        self.geral_tab.set_fps(int(camera_cfg.get("fps", 30)))
        self.show_skeleton_checkbox.setChecked(bool(camera_cfg.get("show_skeleton", True)))

        self.obs_host.setText(obs_cfg.get("host", "localhost"))
        self.obs_port.setValue(int(obs_cfg.get("port", 4455)))
        self.obs_password.setText(obs_cfg.get("password", ""))

        self._rebuild_gesture_grid()
        self._refresh_gesture_feature_visibility()
        self._refresh_health_panels()

    def _get_current_binding(self):
        return self.config.setdefault("gestures", {}).setdefault("bindings", {}).setdefault(
            self.current_gesture,
            {
                "enabled": True,
                "hold_time": self.config["gestures"]["default_hold_time"],
                "cooldown": self.config["gestures"]["default_cooldown"],
                "scene": "",
                "play_sound": False,
                "sound_file": "",
                "hotkey": "",
                "use_scene": False,
                "use_sound": False,
                "use_hotkey": False,
            },
        )

    def select_gesture(self, gesture):
        if gesture not in self.gesture_buttons:
            return

        self.current_gesture = gesture
        for name, btn in self.gesture_buttons.items():
            btn.setChecked(name == gesture)

        cfg = self.config.get("gestures", {}).get("bindings", {}).get(gesture, {})

        self._updating_gesture_form = True
        self.selected_gesture_label.setText(f"Gesto selecionado: {gesture}")
        
        # Hold time: converter para float (2.0-5.0)
        hold_time_seconds = float(cfg.get("hold_time", 2.0))
        hold_time_seconds = max(0.5, min(5.0, hold_time_seconds))  # Garantir 0.5-5.0s
        self.hold_value_spinbox.setValue(hold_time_seconds)
        self.hold_slider.setValue(int(hold_time_seconds * 10))  # Converter para slider
        
        # Cooldown: converter para float (2.0-20.0)
        cooldown_seconds = float(cfg.get("cooldown", 2.0))
        cooldown_seconds = max(2.0, min(20.0, cooldown_seconds))  # Garantir 2.0-20.0s
        self.cooldown_value_spinbox.setValue(cooldown_seconds)
        self.cooldown_slider.setValue(int(cooldown_seconds * 10))  # Converter para slider
        
        self.scene_action_checkbox.setChecked(bool(cfg.get("use_scene", bool(cfg.get("scene", "")))))
        self.sound_action_checkbox.setChecked(bool(cfg.get("use_sound", bool(cfg.get("play_sound", False)))))
        self.hotkey_action_checkbox.setChecked(bool(cfg.get("use_hotkey", bool(cfg.get("hotkey", "")))))
        self.scene_edit.setText(cfg.get("scene", ""))
        self.sound_file_edit.setText(cfg.get("sound_file", ""))
        self.hotkey_edit.setText(cfg.get("hotkey", ""))
        self._updating_gesture_form = False

        self._refresh_gesture_feature_visibility()

    def on_hold_slider_changed(self):
        """Sincroniza slider para spinbox quando slider muda."""
        if not self._updating_gesture_form:
            seconds = self.hold_slider.value() / 10.0
            self.hold_value_spinbox.blockSignals(True)
            self.hold_value_spinbox.setValue(seconds)
            self.hold_value_spinbox.blockSignals(False)

    def on_hold_spinbox_changed(self):
        """Sincroniza spinbox para slider quando spinbox muda."""
        if not self._updating_gesture_form:
            self.hold_slider.blockSignals(True)
            self.hold_slider.setValue(int(self.hold_value_spinbox.value() * 10))
            self.hold_slider.blockSignals(False)

    def on_cooldown_slider_changed(self):
        """Sincroniza slider para spinbox quando slider muda."""
        if not self._updating_gesture_form:
            seconds = self.cooldown_slider.value() / 10.0
            self.cooldown_value_spinbox.blockSignals(True)
            self.cooldown_value_spinbox.setValue(seconds)
            self.cooldown_value_spinbox.blockSignals(False)

    def on_cooldown_spinbox_changed(self):
        """Sincroniza spinbox para slider quando spinbox muda."""
        if not self._updating_gesture_form:
            self.cooldown_slider.blockSignals(True)
            self.cooldown_slider.setValue(int(self.cooldown_value_spinbox.value() * 10))
            self.cooldown_slider.blockSignals(False)


    def _refresh_gesture_feature_visibility(self):
        scene_enabled = self.scene_action_checkbox.isChecked()
        sound_enabled = self.sound_action_checkbox.isChecked()
        hotkey_enabled = self.hotkey_action_checkbox.isChecked()

        self.scene_edit.setEnabled(scene_enabled)
        self.sound_file_edit.setEnabled(sound_enabled)
        self.browse_sound_button.setEnabled(sound_enabled)
        self.hotkey_edit.setEnabled(hotkey_enabled)

    def on_current_gesture_changed(self):
        if self._updating_gesture_form:
            return

        binding = self._get_current_binding()
        binding["enabled"] = self.current_gesture in set(self._active_gestures())
        binding["hold_time"] = float(self.hold_value_spinbox.value())
        binding["cooldown"] = float(self.cooldown_value_spinbox.value())
        binding["use_scene"] = self.scene_action_checkbox.isChecked()
        binding["use_sound"] = self.sound_action_checkbox.isChecked()
        binding["use_hotkey"] = self.hotkey_action_checkbox.isChecked()
        binding["scene"] = self.scene_edit.text().strip()
        binding["play_sound"] = self.sound_action_checkbox.isChecked()
        binding["sound_file"] = self.sound_file_edit.text().strip()
        binding["hotkey"] = self.hotkey_edit.text().strip()

        self._refresh_gesture_feature_visibility()
        self.salvar_config_automatico()

        if self.engine and self.engine.isRunning():
            gestures_cfg = self.config.setdefault("gestures", {})
            self.engine.gesture_bindings = gestures_cfg.get("bindings", {})
            self.engine.mapa_cenas = gestures_cfg.get("scene_map", {})
            self.engine._normalize_gesture_keys()

    def on_show_skeleton_changed(self, checked):
        self.config.setdefault("camera", {})
        self.config["camera"]["show_skeleton"] = bool(checked)

    def on_dynamic_setting_changed(self, *_):
        self.config.setdefault("camera", {})
        self.config["camera"]["show_skeleton"] = self.show_skeleton_checkbox.isChecked()

        binding = self._get_current_binding()
        binding["hold_time"] = self.hold_slider.value() / 10
        binding["cooldown"] = self.cooldown_slider.value() / 10

        gestures_cfg = self.config.setdefault("gestures", {})

        self.salvar_config_automatico()

        if not (self.engine and self.engine.isRunning()):
            return

        self.engine.show_skeleton = self.config["camera"]["show_skeleton"]
        self.engine.gesture_bindings = gestures_cfg.get("bindings", {})
        self.engine.mapa_cenas = gestures_cfg.get("scene_map", {})
        self.engine.tempo_minimo = float(binding["hold_time"])
        self.engine.cooldown = float(binding["cooldown"])
        self.engine._normalize_gesture_keys()

    def select_sound_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo de som",
            "",
            "Áudio (*.wav *.mp3 *.ogg);;Todos os arquivos (*)",
        )
        if file_path:
            self.sound_file_edit.setText(file_path)

    def on_modo_changed(self, modo):
        self.config["modo"] = modo
        self.config.setdefault("camera", {})
        self.config["camera"]["enable_virtual_camera"] = modo == "obs"
        self._refresh_health_panels()
        self.salvar_config_automatico()

    def on_camera_changed(self, _value):
        selected_index = self.camera_device_combo.currentData()
        if selected_index is None:
            selected_index = self.camera_device_combo.currentIndex()
        camera_cfg = self.config.setdefault("camera", {})
        camera_cfg["index"] = int(selected_index)
        camera_cfg["device_name"] = self.camera_device_combo.currentText().strip()
        self.salvar_config_automatico()

    def on_resolution_changed(self, value):
        if value not in RESOLUTION_PRESETS:
            return

        width, height = RESOLUTION_PRESETS[value]

        self.config.setdefault("camera", {})["width"] = width
        self.config.setdefault("camera", {})["height"] = height
        self.salvar_config_automatico()

    def on_fps_changed(self, value):
        self.config.setdefault("camera", {})["fps"] = int(value)
        self.salvar_config_automatico()

    def on_obs_changed(self):
        self.config.setdefault("obs", {})
        self.config["obs"]["host"] = self.obs_host.text().strip()
        self.config["obs"]["port"] = int(self.obs_port.value())
        self.config["obs"]["password"] = self.obs_password.text()
        self.salvar_config_automatico()

    def testar_conexao_obs(self):
        from integrations.obs_connect_thread import OBSConnectThread

        # Cancelar tentativa anterior: desconectar slots para ignorar sinais obsoletos
        if self._obs_connect_thread is not None:
            try:
                self._obs_connect_thread.connected.disconnect()
                self._obs_connect_thread.failed.disconnect()
                self._obs_connect_thread.connecting.disconnect()
            except Exception:
                pass
            self._obs_connect_thread = None

        host = self.obs_host.text().strip()
        port = self.obs_port.value()
        password = self.obs_password.text()

        # D-03: desabilitar botão durante a tentativa e sinalizar estado
        self.test_obs_button.setEnabled(False)
        self.obs_status_label.setText("Conectando...")
        self.obs_footer_label.setText("⏳ OBS: Conectando...")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()  # garante repaint antes de iniciar thread (evita coalescing em falhas rápidas)

        thread = OBSConnectThread(host, port, password)
        thread.connecting.connect(self.on_obs_conectando)
        thread.connected.connect(self.on_obs_conectado)
        thread.failed.connect(self.on_obs_falhou)
        thread.finished.connect(thread.deleteLater)  # Armadilha 2: libera thread ao completar
        self._obs_connect_thread = thread  # Armadilha 4: manter referência viva
        thread.start()

    def on_obs_conectando(self):
        """Slot chamado quando a thread inicia a tentativa de conexão."""
        self.obs_status_label.setText("Conectando...")
        self.obs_footer_label.setText("⏳ OBS: Conectando...")

    def on_obs_conectado(self, obs_controller):
        """Slot chamado quando a conexão OBS é estabelecida com sucesso."""
        self.test_obs_button.setEnabled(True)
        self.obs_status_label.setText("Status: Conectado ✅")
        self.obs_footer_label.setText("🟢 OBS: Conectado")
        # Atribuir OBSController à engine via método dedicado (co-localiza as duas escritas)
        if self.engine and self.engine.isRunning():
            self.engine.set_obs_controller(obs_controller)
        self._refresh_health_panels()
        self._obs_connect_thread = None

    def on_obs_falhou(self, mensagem):
        """Slot chamado quando a tentativa de conexão OBS falha."""
        self.test_obs_button.setEnabled(True)
        self.obs_status_label.setText(mensagem)  # mensagem acionável detalhada (D-08)
        self.obs_footer_label.setText(self._resumir_footer_obs(mensagem))
        self._refresh_health_panels()
        self._obs_connect_thread = None

    def _resumir_footer_obs(self, mensagem):
        """Delega ao mapeamento co-localizado com _classificar_erro."""
        return _resumir_footer_obs_fn(mensagem)

    def start_engine(self):
        erros, avisos = self._validar_config_execucao()

        if erros:
            mensagem = "\n".join(f"• {erro}" for erro in erros)
            QMessageBox.critical(
                self,
                "Configuração inválida",
                f"Corrija os itens abaixo antes de iniciar:\n\n{mensagem}",
            )
            self.update_status("Configuração inválida para iniciar")
            return

        if avisos:
            mensagem = "\n".join(f"• {aviso}" for aviso in avisos)
            resposta = QMessageBox.question(
                self,
                "Avisos de configuração",
                f"Existem avisos de configuração:\n\n{mensagem}\n\nDeseja iniciar mesmo assim?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resposta != QMessageBox.Yes:
                self.update_status("Inicialização cancelada")
                return

        self.salvar_config_automatico()

        if self.engine and self.engine.isRunning():
            self.update_status("Engine já está em execução")
            return

        self.engine = GestureEngine(self.config)
        self.engine.frame_ready.connect(self.update_frame)
        self.engine.status_changed.connect(self.update_status)
        self.engine.start()

        self.status_label.setText("Status: Rodando")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.set_config_enabled(False)
        self._refresh_health_panels()

    def stop_engine(self):
        if not self.engine:
            self.update_status("Engine já está parada")
            return

        try:
            self.engine.finished.disconnect()
        except Exception:
            pass

        self.engine.finished.connect(self.on_engine_finished)
        self.engine.stop()

        self.status_label.setText("Status: Parado")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._refresh_health_panels()

    def restart_engine(self):
        if self.engine and self.engine.isRunning():
            self.engine.finished.connect(self._on_reiniciar_apos_parada)
            self.stop_engine()
        else:
            self.start_engine()

    def _on_reiniciar_apos_parada(self):
        try:
            self.engine.finished.disconnect(self._on_reiniciar_apos_parada)
        except Exception:
            pass
        self.start_engine()

    def closeEvent(self, event):
        # Encerrar thread de conexão OBS em andamento
        if self._obs_connect_thread is not None:
            try:
                self._obs_connect_thread.connected.disconnect()
                self._obs_connect_thread.failed.disconnect()
                self._obs_connect_thread.connecting.disconnect()
            except Exception:
                pass
            self._obs_connect_thread.wait(3000)
            self._obs_connect_thread = None

        # Encerrar engine de gestos
        if self.engine and self.engine.isRunning():
            self.engine.stop()

        super().closeEvent(event)

    def _validar_config_execucao(self):
        erros = []
        avisos = []

        modo = self.config.get("modo", "test")
        obs_cfg = self.config.get("obs", {})
        bindings = self.config.get("gestures", {}).get("bindings", {})
        active_set = set(self._active_gestures())

        if modo == "obs":
            if not str(obs_cfg.get("host", "")).strip():
                erros.append("Host do OBS está vazio")
            porta = int(obs_cfg.get("port", 0) or 0)
            if porta <= 0:
                erros.append("Porta do OBS inválida")

        gestos_ativos = [
            (nome, cfg)
            for nome, cfg in bindings.items()
            if nome in active_set
        ]

        if not gestos_ativos:
            avisos.append("Nenhum gesto está ativado")

        tem_alguma_acao = False
        for nome, cfg in gestos_ativos:
            usa_cena = bool(cfg.get("use_scene", False))
            usa_som = bool(cfg.get("use_sound", False))
            usa_atalho = bool(cfg.get("use_hotkey", False))

            if not (usa_cena or usa_som or usa_atalho):
                avisos.append(f"Gesto {nome} está ativo, mas sem funcionalidade selecionada")
                continue

            tem_alguma_acao = True

            if usa_cena and not str(cfg.get("scene", "")).strip():
                erros.append(f"Gesto {nome}: cena está vazia")

            if usa_som:
                arquivo_som = str(cfg.get("sound_file", "")).strip()
                if not arquivo_som:
                    erros.append(f"Gesto {nome}: arquivo de som está vazio")
                elif not os.path.exists(arquivo_som):
                    avisos.append(f"Gesto {nome}: arquivo de som não encontrado no caminho informado")

            if usa_atalho and not str(cfg.get("hotkey", "")).strip():
                avisos.append(f"Gesto {nome}: atalho está vazio")

            hold_time = float(cfg.get("hold_time", 0.7))
            cooldown = float(cfg.get("cooldown", 2.0))
            if hold_time < 0.1:
                erros.append(f"Gesto {nome}: tempo de resposta deve ser >= 0.1s")
            if cooldown < 0:
                erros.append(f"Gesto {nome}: cooldown não pode ser negativo")

        if not tem_alguma_acao and gestos_ativos:
            avisos.append("Nenhum gesto ativo possui ação efetiva")

        return erros, avisos

    def on_engine_finished(self):
        self.set_config_enabled(True)
        self.status_label.setText("Status: Parado")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._clear_preview()
        self.engine = None
        self._refresh_health_panels()

    def salvar_config(self):
        self.salvar_config_automatico()
        self.status_label.setText("Config salva!")

    def _sync_scene_map_from_bindings(self):
        gestures_cfg = self.config.setdefault("gestures", {})
        bindings = gestures_cfg.setdefault("bindings", {})
        gestures_cfg["scene_map"] = {
            gesture: cfg.get("scene", "")
            for gesture, cfg in bindings.items()
            if cfg.get("scene", "")
        }

    def salvar_config_automatico(self):
        # Agenda o save com debounce de 500ms. start() reinicia o timer se ja
        # estava contando, entao callsites rapidos (ex: arrastar slider) colapsam
        # em um unico write.
        self._save_timer.start(500)

    def _do_save_config(self):
        # Executado na main thread Qt quando o timer dispara (500ms apos o ultimo
        # agendamento). Faz write atomico via tempfile + os.replace para nunca
        # deixar config.json parcial se o processo morrer no meio.
        self._sync_scene_map_from_bindings()
        try:
            dir_path = self._config_path.parent
            fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                os.replace(tmp_path, str(self._config_path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as exc:
            logger.error("Falha ao salvar configuracao: %s", exc)

    def set_config_enabled(self, enabled):
        self.camera_device_combo.setEnabled(enabled)
        for button in self.resolution_buttons.values():
            button.setEnabled(enabled)
        for button in self.fps_buttons.values():
            button.setEnabled(enabled)

    def update_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = frame.shape
        bytes_per_line = ch * w

        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.preview_label.setPixmap(
            pixmap.scaled(
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
        # Rotear mensagens OBS do startup da engine (Plano 03) ao rodapé
        if text == "OBS conectado":
            self.obs_footer_label.setText("🟢 OBS: Conectado")
        elif text.startswith("OBS:"):
            mensagem_obs = text[len("OBS:"):].strip()
            self.obs_footer_label.setText(self._resumir_footer_obs(mensagem_obs))

    def _append_log(self, message):
        if not message:
            return
        self.log_view.appendPlainText(message)

    def _set_health_label(self, label_widget, titulo, estado, detalhe):
        colors = {
            "ok": "#22c55e",
            "warn": "#f59e0b",
            "error": "#ef4444",
            "idle": "#94a3b8",
        }
        color = colors.get(estado, colors["idle"])
        label_widget.setText(f"● {titulo}: {detalhe}")
        label_widget.setStyleSheet(f"color: {color}; font-weight: 600;")

    def _refresh_health_panels(self):
        modo = self.config.get("modo", "test")
        bindings = self.config.get("gestures", {}).get("bindings", {})
        active_set = set(self._active_gestures())

        camera_running = bool(self.engine and self.engine.isRunning())
        if camera_running:
            self._set_health_label(self.health_camera, "Câmera", "ok", "Em execução")
        else:
            selected_name = self.camera_device_combo.currentText() or "Câmera"
            self._set_health_label(self.health_camera, "Câmera", "idle", f"Pronta ({selected_name})")

        if modo == "obs":
            obs_status_text = self.obs_status_label.text().lower()
            if "conectado" in obs_status_text and "falha" not in obs_status_text:
                self._set_health_label(self.health_obs, "OBS", "ok", "Conectado")
            elif camera_running:
                self._set_health_label(self.health_obs, "OBS", "warn", "Aguardando conexão")
            else:
                self._set_health_label(self.health_obs, "OBS", "idle", "Não testado")
        else:
            self._set_health_label(self.health_obs, "OBS", "idle", "Desativado (modo test)")

        ativos = [gesture for gesture in active_set if gesture in bindings]
        if not ativos:
            self._set_health_label(self.health_gestos, "Gestos", "warn", "Nenhum gesto ativo")
        else:
            self._set_health_label(self.health_gestos, "Gestos", "ok", f"{len(ativos)} gesto(s) ativos")

    def _update_runtime_health_from_status(self, text):
        text_lower = (text or "").lower()

        if "falha ao iniciar câmera" in text_lower:
            self._set_health_label(self.health_camera, "Câmera", "error", "Falha ao iniciar")
            return

        if "câmera iniciada" in text_lower:
            self._set_health_label(self.health_camera, "Câmera", "ok", "Conectada")

        if "obs conectado" in text_lower:
            self._set_health_label(self.health_obs, "OBS", "ok", "Conectado")
        elif "falha ao conectar obs" in text_lower:
            self._set_health_label(self.health_obs, "OBS", "error", "Falha de conexão")

        if "engine parada" in text_lower:
            self._refresh_health_panels()
