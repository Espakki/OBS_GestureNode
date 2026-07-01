import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from util.logger import get_logger

logger = get_logger(__name__)


class GestureMixin:

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

    def _resolve_asset_path(self, icon_path):
        if not icon_path:
            return ""
        if os.path.isabs(icon_path):
            return icon_path
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", icon_path))

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

    def select_gesture(self, gesture):
        if gesture not in self.gesture_buttons:
            return

        self.current_gesture = gesture
        for name, btn in self.gesture_buttons.items():
            btn.setChecked(name == gesture)

        cfg = self.config.get("gestures", {}).get("bindings", {}).get(gesture, {})

        self._updating_gesture_form = True
        self.selected_gesture_label.setText(f"Gesto selecionado: {gesture}")

        hold_time_seconds = float(cfg.get("hold_time", 2.0))
        hold_time_seconds = max(0.5, min(5.0, hold_time_seconds))
        self.hold_value_spinbox.setValue(hold_time_seconds)
        self.hold_slider.setValue(int(hold_time_seconds * 10))

        cooldown_seconds = float(cfg.get("cooldown", 2.0))
        cooldown_seconds = max(2.0, min(20.0, cooldown_seconds))
        self.cooldown_value_spinbox.setValue(cooldown_seconds)
        self.cooldown_slider.setValue(int(cooldown_seconds * 10))

        self.scene_action_checkbox.setChecked(bool(cfg.get("use_scene", bool(cfg.get("scene", "")))))
        self.sound_action_checkbox.setChecked(bool(cfg.get("use_sound", bool(cfg.get("play_sound", False)))))
        self.hotkey_action_checkbox.setChecked(bool(cfg.get("use_hotkey", bool(cfg.get("hotkey", "")))))
        self.scene_edit.setText(cfg.get("scene", ""))
        self.sound_file_edit.setText(cfg.get("sound_file", ""))
        self.hotkey_edit.setText(cfg.get("hotkey", ""))
        self._updating_gesture_form = False

        self._refresh_gesture_feature_visibility()

    def on_hold_slider_changed(self):
        if not self._updating_gesture_form:
            seconds = self.hold_slider.value() / 10.0
            self.hold_value_spinbox.blockSignals(True)
            self.hold_value_spinbox.setValue(seconds)
            self.hold_value_spinbox.blockSignals(False)

    def on_hold_spinbox_changed(self):
        if not self._updating_gesture_form:
            self.hold_slider.blockSignals(True)
            self.hold_slider.setValue(int(self.hold_value_spinbox.value() * 10))
            self.hold_slider.blockSignals(False)

    def on_cooldown_slider_changed(self):
        if not self._updating_gesture_form:
            seconds = self.cooldown_slider.value() / 10.0
            self.cooldown_value_spinbox.blockSignals(True)
            self.cooldown_value_spinbox.setValue(seconds)
            self.cooldown_value_spinbox.blockSignals(False)

    def on_cooldown_spinbox_changed(self):
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
