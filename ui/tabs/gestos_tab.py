from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)


class HotkeyLineEdit(QLineEdit):
    """QLineEdit customizado para capturar atalhos de teclado (estilo OBS)."""

    hotkeyCommitted = Signal(str)
    captureStarted = Signal()
    captureCanceled = Signal()
    
    def __init__(self):
        super().__init__()
        self._capturing = False
        self._previous_value = ""
        self._pressed_modifiers = set()
        self._idle_placeholder = "Clique para capturar (ESC para cancelar)"
        self._capture_placeholder = "Pressione as teclas..."
        self.setPlaceholderText(self._idle_placeholder)
        self.setReadOnly(True)  # Campo é read-only por padrão
    
    def mousePressEvent(self, event):
        """Quando clica no campo, entra em modo de captura."""
        super().mousePressEvent(event)
        if not self._capturing:
            self._start_capture()
    
    def _start_capture(self):
        """Inicia a captura de hotkey."""
        if self._capturing:
            return
        
        self._capturing = True
        self._previous_value = self.text()
        self._pressed_modifiers = set()
        self.blockSignals(True)
        self.clear()
        self.setPlaceholderText(self._capture_placeholder)
        self.blockSignals(False)
        self.setStyleSheet("background-color: #4CAF50; color: white; border: 1px solid #2e7d32;")
        self.setFocus()
        self.captureStarted.emit()

    def _finish_capture(self, hotkey_str):
        self._capturing = False
        self._pressed_modifiers = set()
        self.blockSignals(True)
        self.setPlaceholderText(self._idle_placeholder)
        self.setText(hotkey_str)
        self.blockSignals(False)
        self.setStyleSheet("")
        self.hotkeyCommitted.emit(hotkey_str)

    def _cancel_capture(self):
        self._capturing = False
        self._pressed_modifiers = set()
        self.blockSignals(True)
        self.setPlaceholderText(self._idle_placeholder)
        self.setText(self._previous_value)
        self.blockSignals(False)
        self.setStyleSheet("")
        self.captureCanceled.emit()

    def _build_hotkey_from_event(self, event):
        modifiers = self._ordered_modifiers_from_flags(event.modifiers())
        if not modifiers:
            modifiers = self._ordered_modifiers_from_state()
        if not modifiers:
            return ""

        key_name = self._format_key_name(event)
        if not key_name:
            text = (event.text() or "").strip()
            if len(text) == 1 and text.isascii():
                key_name = text.upper()
            elif text:
                key_name = text.capitalize()

        if not key_name:
            return ""

        return "+".join(modifiers + [key_name])

    def _commit_if_possible(self, event):
        hotkey_str = self._build_hotkey_from_event(event)
        if not hotkey_str:
            return False

        self._finish_capture(hotkey_str)
        return True
    
    def keyPressEvent(self, event):
        """Captura eventos de tecla."""
        if not self._capturing:
            super().keyPressEvent(event)
            return
        
        if event.isAutoRepeat():
            return  # Ignora auto-repeat

        key_code = event.key()

        if key_code == Qt.Key_Escape:
            self._cancel_capture()
            return

        if key_code in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            self._pressed_modifiers.add(key_code)
            return

        self._commit_if_possible(event)
    
    def keyReleaseEvent(self, event):
        """Mantém consumo dos eventos durante a captura."""
        if not self._capturing:
            super().keyReleaseEvent(event)
            return
        
        if event.isAutoRepeat():
            return  # Ignora auto-repeat

        key_code = event.key()
        if key_code in self._pressed_modifiers:
            self._pressed_modifiers.discard(key_code)
            return

        if key_code not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            self._commit_if_possible(event)

    def focusOutEvent(self, event):
        if self._capturing:
            self._cancel_capture()
        super().focusOutEvent(event)

    def _ordered_modifiers_from_flags(self, flags):
        ordered = []
        if flags & Qt.ControlModifier:
            ordered.append("Ctrl")
        if flags & Qt.AltModifier:
            ordered.append("Alt")
        if flags & Qt.ShiftModifier:
            ordered.append("Shift")
        if flags & Qt.MetaModifier:
            ordered.append("Win")
        return ordered

    def _ordered_modifiers_from_state(self):
        ordered = []
        if Qt.Key_Control in self._pressed_modifiers:
            ordered.append("Ctrl")
        if Qt.Key_Alt in self._pressed_modifiers:
            ordered.append("Alt")
        if Qt.Key_Shift in self._pressed_modifiers:
            ordered.append("Shift")
        if Qt.Key_Meta in self._pressed_modifiers:
            ordered.append("Win")
        return ordered

    def _format_key_name(self, event):
        key_code = event.key()

        # Letras A-Z
        if Qt.Key_A <= key_code <= Qt.Key_Z:
            return chr(key_code)

        # Numeros 0-9
        if Qt.Key_0 <= key_code <= Qt.Key_9:
            return chr(key_code)

        # Numpad 0-9
        if event.modifiers() & Qt.KeypadModifier and Qt.Key_0 <= key_code <= Qt.Key_9:
            return chr(key_code)

        # F1-F24
        if Qt.Key_F1 <= key_code <= Qt.Key_F24:
            return f"F{key_code - Qt.Key_F1 + 1}"

        key_name_by_code = {
            Qt.Key_Space: "Space",
            Qt.Key_Tab: "Tab",
            Qt.Key_Backtab: "Tab",
            Qt.Key_Return: "Enter",
            Qt.Key_Enter: "Enter",
            Qt.Key_Backspace: "Backspace",
            Qt.Key_Delete: "Delete",
            Qt.Key_Insert: "Insert",
            Qt.Key_Home: "Home",
            Qt.Key_End: "End",
            Qt.Key_PageUp: "PageUp",
            Qt.Key_PageDown: "PageDown",
            Qt.Key_Left: "Left",
            Qt.Key_Right: "Right",
            Qt.Key_Up: "Up",
            Qt.Key_Down: "Down",
            Qt.Key_Escape: "Esc",
            Qt.Key_Pause: "Pause",
            Qt.Key_Print: "PrintScreen",
            Qt.Key_ScrollLock: "ScrollLock",
            Qt.Key_CapsLock: "CapsLock",
            Qt.Key_NumLock: "NumLock",
            Qt.Key_Menu: "Menu",
            Qt.Key_Help: "Help",
        }
        if key_code in key_name_by_code:
            return key_name_by_code[key_code]

        punctuation_by_key = {
            Qt.Key_Plus: "Plus",
            Qt.Key_Minus: "-",
            Qt.Key_Equal: "=",
            Qt.Key_Slash: "/",
            Qt.Key_Backslash: "\\",
            Qt.Key_Comma: ",",
            Qt.Key_Period: ".",
            Qt.Key_Semicolon: ";",
            Qt.Key_Apostrophe: "'",
            Qt.Key_BracketLeft: "[",
            Qt.Key_BracketRight: "]",
            Qt.Key_QuoteLeft: "`",
        }
        if key_code in punctuation_by_key:
            return punctuation_by_key[key_code]

        normalized = QKeySequence(key_code).toString(QKeySequence.NativeText).strip()
        if not normalized:
            return ""

        # Ignora chars especiais de layout/AltGr (ex: ©åéßæ), mas mantém pontuação ASCII.
        if len(normalized) == 1 and not normalized.isascii():
            return ""

        if normalized == "+":
            return "Plus"

        allowed = {
            "Space", "Tab", "Enter", "Return", "Backspace", "Delete",
            "Insert", "Home", "End", "PageUp", "PageDown", "Up", "Down",
            "Left", "Right"
        }
        if normalized.startswith("F") and normalized[1:].isdigit():
            return normalized.upper()
        if normalized in allowed:
            return normalized
        if len(normalized) == 1 and normalized.isascii():
            return normalized.upper()
        return ""


class GestosTab(QWidget):
    def __init__(self):
        super().__init__()
        self._gesture_buttons = []

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        title = QLabel("Configuração de Gestos")
        title.setObjectName("title")
        layout.addWidget(title)

        self.grid_container = QFrame()
        self.grid_container.setObjectName("card")
        self.grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(10)
        layout.addWidget(self.grid_container)

        self.choose_gestures_button = QPushButton("Selecionar gestos ativos")
        self.choose_gestures_button.setObjectName("ghost")
        self.choose_gestures_button.setMinimumHeight(38)
        layout.addWidget(self.choose_gestures_button)

        self.gesture_editor = QFrame()
        self.gesture_editor.setObjectName("card")
        editor_layout = QVBoxLayout(self.gesture_editor)
        editor_layout.setSpacing(12)

        self.selected_gesture_label = QLabel("Gesto selecionado: -")
        editor_layout.addWidget(self.selected_gesture_label)

        hold_row = QHBoxLayout()
        hold_row.setSpacing(10)
        hold_label = QLabel("Tempo de resposta:")
        hold_label.setMinimumWidth(140)
        hold_row.addWidget(hold_label)
        self.hold_slider = QSlider(Qt.Horizontal)
        self.hold_slider.setRange(20, 50)  # 2.0 a 5.0s (multiplicador de 0.1)
        self.hold_slider.setMinimumHeight(30)
        self.hold_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hold_value_spinbox = QDoubleSpinBox()
        self.hold_value_spinbox.setRange(2.0, 5.0)  # 2.0 a 5.0 segundos
        self.hold_value_spinbox.setSingleStep(1.0)  # Incremento de 1s com ↑↓ (mas permite digitar decimais)
        self.hold_value_spinbox.setDecimals(1)  # 1 casa decimal
        self.hold_value_spinbox.setSuffix("s")
        self.hold_value_spinbox.setMinimumWidth(80)
        self.hold_value_spinbox.setAlignment(Qt.AlignCenter)
        # Tooltip para indicar que é clicável
        self.hold_value_spinbox.setToolTip("Clique para editar ou use as setas (2.0-5.0s)")
        hold_row.addWidget(self.hold_slider)
        hold_row.addWidget(self.hold_value_spinbox)
        editor_layout.addLayout(hold_row)

        cooldown_row = QHBoxLayout()
        cooldown_row.setSpacing(10)
        cooldown_label = QLabel("Cooldown:")
        cooldown_label.setMinimumWidth(140)
        cooldown_row.addWidget(cooldown_label)
        self.cooldown_slider = QSlider(Qt.Horizontal)
        self.cooldown_slider.setRange(20, 200)  # 2.0 a 20.0s (multiplicador de 0.1)
        self.cooldown_slider.setMinimumHeight(30)
        self.cooldown_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cooldown_value_spinbox = QDoubleSpinBox()
        self.cooldown_value_spinbox.setRange(2.0, 20.0)  # 2.0 a 20.0 segundos
        self.cooldown_value_spinbox.setSingleStep(1.0)  # Incremento de 1s com ↑↓ (mas permite digitar decimais)
        self.cooldown_value_spinbox.setDecimals(1)  # 1 casa decimal
        self.cooldown_value_spinbox.setSuffix("s")
        self.cooldown_value_spinbox.setMinimumWidth(80)
        self.cooldown_value_spinbox.setAlignment(Qt.AlignCenter)
        # Tooltip para indicar que é clicável
        self.cooldown_value_spinbox.setToolTip("Clique para editar ou use as setas (2.0-20.0s)")
        cooldown_row.addWidget(self.cooldown_slider)
        cooldown_row.addWidget(self.cooldown_value_spinbox)
        editor_layout.addLayout(cooldown_row)

        feature_label = QLabel("Funcionalidades do gesto:")
        feature_label.setObjectName("muted")
        editor_layout.addWidget(feature_label)
        self.scene_action_checkbox = QCheckBox("Trocar cena")
        self.sound_action_checkbox = QCheckBox("Emitir som")
        self.hotkey_action_checkbox = QCheckBox("Acionar atalho")
        self.scene_action_checkbox.setMinimumWidth(125)
        self.sound_action_checkbox.setMinimumWidth(125)
        self.hotkey_action_checkbox.setMinimumWidth(125)

        self.scene_row = QWidget()
        self.scene_row.setObjectName("transparentRow")
        scene_row_layout = QHBoxLayout(self.scene_row)
        scene_row_layout.setContentsMargins(0, 0, 0, 0)
        scene_row_layout.setSpacing(8)
        scene_row_layout.addWidget(self.scene_action_checkbox)
        self.scene_edit = QLineEdit()
        self.scene_edit.setPlaceholderText("Ex: Cena_Principal")
        self.scene_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scene_row_layout.addWidget(self.scene_edit)
        editor_layout.addWidget(self.scene_row)

        self.sound_row = QWidget()
        self.sound_row.setObjectName("transparentRow")
        sound_row_layout = QHBoxLayout(self.sound_row)
        sound_row_layout.setContentsMargins(0, 0, 0, 0)
        sound_row_layout.setSpacing(8)
        sound_row_layout.addWidget(self.sound_action_checkbox)
        self.sound_file_edit = QLineEdit()
        self.sound_file_edit.setPlaceholderText("Ex: C:/audios/efeito.wav")
        self.sound_file_edit.setMinimumWidth(0)
        self.sound_file_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.browse_sound_button = QPushButton("Selecionar")
        self.browse_sound_button.setObjectName("ghost")
        self.browse_sound_button.setMinimumWidth(110)
        sound_row_layout.addWidget(self.sound_file_edit)
        sound_row_layout.addWidget(self.browse_sound_button)
        sound_row_layout.setStretch(1, 1)
        editor_layout.addWidget(self.sound_row)

        self.hotkey_row = QWidget()
        self.hotkey_row.setObjectName("transparentRow")
        hotkey_row_layout = QHBoxLayout(self.hotkey_row)
        hotkey_row_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_row_layout.setSpacing(8)
        hotkey_row_layout.addWidget(self.hotkey_action_checkbox)
        self.hotkey_edit = HotkeyLineEdit()
        self.hotkey_edit.setPlaceholderText("Clique para capturar (ESC para cancelar)")
        self.hotkey_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hotkey_row_layout.addWidget(self.hotkey_edit)
        hotkey_row_layout.setStretch(1, 1)  # Faz o campo expandir
        
        editor_layout.addWidget(self.hotkey_row)

        layout.addWidget(self.gesture_editor)
        layout.addStretch(1)

    def clear_gesture_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._gesture_buttons = []

    def add_gesture_button(self, row, col, text, callback):
        button = QPushButton(text)
        button.setObjectName("gestureBtn")
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        parts = text.split("\n", 1)
        emoji_text = parts[0] if parts else text
        button.setProperty("emojiText", emoji_text)
        button.setProperty("fullText", text)
        button.clicked.connect(callback)
        self.grid_layout.addWidget(button, row, col)
        self.grid_layout.setRowStretch(row + 1, 1)
        self._gesture_buttons.append(button)
        self._refresh_gesture_button_texts()
        return button

    def _refresh_gesture_button_texts(self):
        for button in self._gesture_buttons:
            compact = button.width() < 140 or button.height() < 76
            if compact:
                button.setText(button.property("emojiText") or "")
            else:
                button.setText(button.property("fullText") or "")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_gesture_button_texts()
