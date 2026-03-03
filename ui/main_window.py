import json
import os
import cv2

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
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
    QVBoxLayout,
    QWidget,
)

from engine.gesture_engine import GestureEngine
from ui.tabs.geral_tab import GeralTab
from ui.tabs.gestos_tab import GestosTab
from ui.tabs.obs_tab import OBSTab
from util.logger import get_logger


logger = get_logger(__name__)


GESTURE_ALIASES = {
    "JOIHA": "THUMBS_UP",
    "MÃO_ABERTA": "OPEN_HAND",
    "MAO_ABERTA": "OPEN_HAND",
    "SOCO": "FIST",
    "APONTANDO_CIMA": "POINT",
}


class MainWindow(QMainWindow):
    ALL_GESTURES = [
        ("V", "✌"),
        ("Joinha", "👍"),
        ("Mão aberta", "✋"),
        ("Punho", "👊"),
        ("Apontando p/ cima", "☝"),
        ("ROCK", "🤘"),
        ("TRES", "3️⃣"),
        ("QUATRO", "4️⃣"),
        ("OK", "👌"),
        ("Me liga", "🤙"),
        ("Deslike", "👎"),
        ("Pinça", "🤏"),
    ]

    def __init__(self, config):
        super().__init__()

        self.setWindowTitle("Gesture OBS Controller")
        self.setMinimumSize(1200, 760)

        self.config = config or {}
        self.engine = None
        self.current_gesture = self.ALL_GESTURES[0][0]
        self._updating_gesture_form = False
        self.gesture_buttons = {}

        self._init_config_schema()
        self._setup_ui()
        self._load_ui_from_config()
        self.salvar_config_automatico()

        self._append_log("Interface inicializada")

    def _init_config_schema(self):
        self.config.setdefault("modo", "test")

        camera_cfg = self.config.setdefault("camera", {})
        camera_cfg.setdefault("index", 0)
        camera_cfg.setdefault("width", 1280)
        camera_cfg.setdefault("height", 720)
        camera_cfg.setdefault("fps", 30)
        camera_cfg.setdefault("enable_virtual_camera", False)
        camera_cfg.setdefault("virtual_camera_device", None)
        camera_cfg.setdefault("show_skeleton", True)

        obs_cfg = self.config.setdefault("obs", {})
        obs_cfg.setdefault("host", "localhost")
        obs_cfg.setdefault("port", 4455)
        obs_cfg.setdefault("password", "")

        gestures_cfg = self.config.setdefault("gestures", {})
        default_hold = gestures_cfg.get("default_hold_time", gestures_cfg.get("hold_time", 0.7))
        default_cooldown = gestures_cfg.get("default_cooldown", gestures_cfg.get("cooldown", 2.0))
        gestures_cfg["default_hold_time"] = float(default_hold)
        gestures_cfg["default_cooldown"] = float(default_cooldown)

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
            normalized[gesture] = {
                "enabled": bool(raw.get("enabled", gesture in gestures_cfg["active_gestures"])),
                "hold_time": float(raw.get("hold_time", gestures_cfg["default_hold_time"])),
                "cooldown": float(raw.get("cooldown", gestures_cfg["default_cooldown"])),
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

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #111418; color: #E6E6E6; font-size: 15px; }
            QTabWidget::pane { border: 1px solid #2a2f36; background: #1a1f26; }
            QTabBar::tab { background: #222831; padding: 10px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-size: 15px; }
            QTabBar::tab:selected { background: #2d3642; color: #ffcc33; }
            QFrame#card { background: #1a1f26; border: 1px solid #2a2f36; border-radius: 10px; }
            QFrame#bottomPanel { background: #1a1f26; border: 1px solid #2a2f36; border-radius: 8px; }
            QWidget#transparentRow { background: transparent; }
            QLabel { font-size: 15px; background: transparent; }
            QCheckBox { spacing: 8px; font-size: 15px; background: transparent; }
            QLabel#title { color: #ffcc33; font-size: 22px; font-weight: 800; background: transparent; }
            QLineEdit, QComboBox, QSpinBox {
                background: #252b33;
                border: 1px solid #3b4654;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 5px;
                color: #f1f1f1;
                min-height: 20px;
            }
            QPushButton { background: #1f6feb; border: none; border-radius: 8px; padding: 10px 14px; color: white; font-weight: 600; font-size: 15px; }
            QPushButton:hover { background: #2c7dff; }
            QPushButton#danger { background: #d63d3d; }
            QPushButton#warning { background: #d08a00; }
            QPushButton#ghost { background: #2a2f36; }
            QPushButton#gestureBtn { background: #252b33; border: 1px solid #3a4655; padding: 15px; max-height: 100px; }
            QPushButton#gestureBtn:checked { border: 2px solid #ffcc33; background: #2f3742; }
            QFrame#card QPushButton { background: #1f6feb; color: white; border: none; }
            QFrame#card QPushButton#danger { background: #d63d3d; color: white; }
            QFrame#card QPushButton#warning { background: #d08a00; color: white; }
            QFrame#card QPushButton#ghost { background: #2a2f36; color: white; }
            QFrame#card QPushButton#gestureBtn { background: #252b33; color: white; }
            QFrame#card QPushButton#gestureBtn:checked { background: #2f3742; color: #ffcc33; }
            QPlainTextEdit { background: #0f1318; border: 1px solid #2a2f36; border-radius: 8px; color: #d4dde8; }
            QSlider { background: transparent; }
            QSlider::groove:horizontal { height: 10px; background: #3a4049; border-radius: 5px; }
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

        self.modo_combo = self.geral_tab.modo_combo
        self.show_skeleton_checkbox = self.geral_tab.show_skeleton_checkbox
        self.health_camera = self.geral_tab.health_camera
        self.health_obs = self.geral_tab.health_obs
        self.health_gestos = self.geral_tab.health_gestos

        self.grid_layout = self.gestos_tab.grid_layout
        self.choose_gestures_button = self.gestos_tab.choose_gestures_button
        self.selected_gesture_label = self.gestos_tab.selected_gesture_label
        self.gesture_enabled_checkbox = self.gestos_tab.gesture_enabled_checkbox
        self.hold_slider = self.gestos_tab.hold_slider
        self.hold_value_label = self.gestos_tab.hold_value_label
        self.cooldown_slider = self.gestos_tab.cooldown_slider
        self.cooldown_value_label = self.gestos_tab.cooldown_value_label
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

        self.modo_combo.currentTextChanged.connect(self.on_modo_changed)
        self.show_skeleton_checkbox.stateChanged.connect(self.on_show_skeleton_changed)

        self.choose_gestures_button.clicked.connect(self.open_gesture_selector_dialog)
        self.gesture_enabled_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.hold_slider.valueChanged.connect(self.on_current_gesture_changed)
        self.cooldown_slider.valueChanged.connect(self.on_current_gesture_changed)
        self.scene_action_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.sound_action_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.hotkey_action_checkbox.stateChanged.connect(self.on_current_gesture_changed)
        self.scene_edit.textChanged.connect(self.on_current_gesture_changed)
        self.sound_file_edit.textChanged.connect(self.on_current_gesture_changed)
        self.hotkey_edit.textChanged.connect(self.on_current_gesture_changed)
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

        right_title = QLabel("Câmera e Execução")
        right_title.setObjectName("title")
        right_layout.addWidget(right_title)

        camera_form = QFormLayout()
        camera_form.setVerticalSpacing(14)
        right_layout.addLayout(camera_form)

        self.camera_index = QSpinBox()
        self.camera_index.setRange(0, 10)
        self.camera_index.valueChanged.connect(self.on_camera_changed)
        camera_form.addRow("Dispositivo:", self.camera_index)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        camera_form.addRow("Resolução:", self.resolution_combo)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 120)
        self.fps_spin.valueChanged.connect(self.on_fps_changed)
        camera_form.addRow("FPS:", self.fps_spin)

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
        bottom_layout.addWidget(self.status_label)

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

        for idx, (gesture, emoji) in enumerate(visible_gestures):
            row = idx // 3
            col = idx % 3
            callback = lambda _=None, g=gesture: self.select_gesture(g)
            btn = self.gestos_tab.add_gesture_button(row, col, f"{emoji}\n{gesture}", callback)
            self.gesture_buttons[gesture] = btn

        if self.current_gesture not in self.gesture_buttons and self.gesture_buttons:
            self.current_gesture = next(iter(self.gesture_buttons.keys()))

        if self.gesture_buttons:
            self.select_gesture(self.current_gesture)

    def open_gesture_selector_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Escolher gestos ativos")
        dialog.resize(420, 520)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.addWidget(QLabel("Selecione os gestos que você quer usar na tela principal:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        active_set = set(self._active_gestures())
        checkboxes = {}
        for gesture, emoji in self.ALL_GESTURES:
            checkbox = QCheckBox(f"{emoji}  {gesture}")
            checkbox.setChecked(gesture in active_set)
            content_layout.addWidget(checkbox)
            checkboxes[gesture] = checkbox

        content_layout.addStretch(1)
        scroll.setWidget(content)
        dialog_layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_layout.addWidget(buttons)

        def on_accept():
            selected = [gesture for gesture, checkbox in checkboxes.items() if checkbox.isChecked()]
            if not selected:
                QMessageBox.warning(dialog, "Seleção inválida", "Selecione pelo menos um gesto.")
                return

            self.config.setdefault("gestures", {})["active_gestures"] = selected
            bindings = self.config.setdefault("gestures", {}).setdefault("bindings", {})
            for gesture, cfg in bindings.items():
                if isinstance(cfg, dict):
                    cfg["enabled"] = gesture in selected

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

        self.modo_combo.setCurrentText(self.config.get("modo", "test"))

        self.camera_index.setValue(int(camera_cfg.get("index", 0)))
        width = int(camera_cfg.get("width", 1280))
        height = int(camera_cfg.get("height", 720))
        resolution = f"{width}x{height}"
        found = self.resolution_combo.findText(resolution)
        if found >= 0:
            self.resolution_combo.setCurrentIndex(found)
        self.fps_spin.setValue(int(camera_cfg.get("fps", 30)))
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
        self.gesture_enabled_checkbox.setChecked(bool(cfg.get("enabled", True)))
        self.hold_slider.setValue(int(float(cfg.get("hold_time", 0.7)) * 10))
        self.cooldown_slider.setValue(int(float(cfg.get("cooldown", 2.0)) * 10))
        self.scene_action_checkbox.setChecked(bool(cfg.get("use_scene", bool(cfg.get("scene", "")))))
        self.sound_action_checkbox.setChecked(bool(cfg.get("use_sound", bool(cfg.get("play_sound", False)))))
        self.hotkey_action_checkbox.setChecked(bool(cfg.get("use_hotkey", bool(cfg.get("hotkey", "")))))
        self.scene_edit.setText(cfg.get("scene", ""))
        self.sound_file_edit.setText(cfg.get("sound_file", ""))
        self.hotkey_edit.setText(cfg.get("hotkey", ""))
        self._updating_gesture_form = False

        self._update_slider_labels()
        self._refresh_gesture_feature_visibility()

    def _update_slider_labels(self):
        self.hold_value_label.setText(f"{self.hold_slider.value() / 10:.1f}s")
        self.cooldown_value_label.setText(f"{self.cooldown_slider.value() / 10:.1f}s")

    def _refresh_gesture_feature_visibility(self):
        self.scene_row.setVisible(self.scene_action_checkbox.isChecked())
        self.sound_row.setVisible(self.sound_action_checkbox.isChecked())
        self.hotkey_row.setVisible(self.hotkey_action_checkbox.isChecked())

    def on_current_gesture_changed(self):
        if self._updating_gesture_form:
            return

        self._update_slider_labels()

        binding = self._get_current_binding()
        binding["enabled"] = self.gesture_enabled_checkbox.isChecked()
        binding["hold_time"] = self.hold_slider.value() / 10
        binding["cooldown"] = self.cooldown_slider.value() / 10
        binding["use_scene"] = self.scene_action_checkbox.isChecked()
        binding["use_sound"] = self.sound_action_checkbox.isChecked()
        binding["use_hotkey"] = self.hotkey_action_checkbox.isChecked()
        binding["scene"] = self.scene_edit.text().strip()
        binding["play_sound"] = self.sound_action_checkbox.isChecked()
        binding["sound_file"] = self.sound_file_edit.text().strip()
        binding["hotkey"] = self.hotkey_edit.text().strip()

        active_set = set(self._active_gestures())
        binding["enabled"] = binding["enabled"] and (self.current_gesture in active_set)

        self._refresh_gesture_feature_visibility()
        self.salvar_config_automatico()

    def on_show_skeleton_changed(self):
        self.config.setdefault("camera", {})
        self.config["camera"]["show_skeleton"] = self.show_skeleton_checkbox.isChecked()
        self.salvar_config_automatico()

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

    def on_camera_changed(self, value):
        self.config.setdefault("camera", {})["index"] = int(value)
        self.salvar_config_automatico()

    def on_resolution_changed(self, value):
        try:
            width_text, height_text = value.lower().split("x")
            width = int(width_text.strip())
            height = int(height_text.strip())
        except Exception:
            return

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
        from integrations.obs_controller import OBSController

        host = self.obs_host.text().strip()
        port = self.obs_port.value()
        password = self.obs_password.text()

        try:
            obs = OBSController(host=host, port=port, password=password)
            obs.connect()
            cenas = obs.listar_cenas()
            if cenas:
                self.obs_status_label.setText("Status: Conectado ✅")
            else:
                self.obs_status_label.setText("Conectado, mas sem cenas")
            obs.disconnect()
        except Exception as exc:
            self.obs_status_label.setText("Falha na conexão ❌")
            logger.exception("Erro ao testar conexão OBS: %s", exc)

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
        running = bool(self.engine and self.engine.isRunning())
        if running:
            self.stop_engine()
        self.start_engine()

    def _validar_config_execucao(self):
        erros = []
        avisos = []

        modo = self.config.get("modo", "test")
        obs_cfg = self.config.get("obs", {})
        bindings = self.config.get("gestures", {}).get("bindings", {})

        if modo == "obs":
            if not str(obs_cfg.get("host", "")).strip():
                erros.append("Host do OBS está vazio")
            porta = int(obs_cfg.get("port", 0) or 0)
            if porta <= 0:
                erros.append("Porta do OBS inválida")

        gestos_ativos = [
            (nome, cfg)
            for nome, cfg in bindings.items()
            if bool(cfg.get("enabled", True))
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
                erros.append(f"Gesto {nome}: atalho está vazio")

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
        self._sync_scene_map_from_bindings()
        with open("config.json", "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)

    def set_config_enabled(self, enabled):
        self.tabs.setEnabled(enabled)
        self.camera_index.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        self.fps_spin.setEnabled(enabled)
        self.restart_button.setEnabled(enabled)

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

    def update_status(self, text):
        self.status_label.setText(text)
        self._append_log(text)
        self._update_runtime_health_from_status(text)

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

        camera_running = bool(self.engine and self.engine.isRunning())
        if camera_running:
            self._set_health_label(self.health_camera, "Câmera", "ok", "Em execução")
        else:
            idx = int(self.config.get("camera", {}).get("index", 0))
            self._set_health_label(self.health_camera, "Câmera", "idle", f"Pronta (índice {idx})")

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

        ativos = [cfg for cfg in bindings.values() if cfg.get("enabled", True)]
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
