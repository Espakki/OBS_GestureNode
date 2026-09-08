import os

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence

from ui import atalho_capturado
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
    QToolButton,
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
        """Delega a `ui/atalho_capturado.py`, que é onde a regra do AltGr mora. Ver D-50."""
        return atalho_capturado.montar_de_evento(event, self._pressed_modifiers)

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
            mods = self._ordered_modifiers_from_state()
            if mods:
                self.blockSignals(True)
                self.setText("+".join(mods) + "+...")
                self.blockSignals(False)
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
            mods = self._ordered_modifiers_from_state()
            self.blockSignals(True)
            self.setText("+".join(mods) + "+..." if mods else "")
            self.blockSignals(False)
            return

        if key_code not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            self._commit_if_possible(event)

    def focusOutEvent(self, event):
        if self._capturing:
            self._cancel_capture()
        super().focusOutEvent(event)

    def _ordered_modifiers_from_flags(self, flags):
        return atalho_capturado.modificadores_de_flags(flags)

    def _ordered_modifiers_from_state(self):
        return atalho_capturado.modificadores_de_teclas(self._pressed_modifiers)

    def _format_key_name(self, event):
        return atalho_capturado.nome_da_tecla(
            event.key(), event.modifiers(), event.text(), event.nativeVirtualKey()
        )


class GestosTab(QWidget):
    """A aba Gestos em Qt Widgets. Mesmo contrato da versão QML."""

    gestoSelecionado = Signal(str)
    escolherGestosPedido = Signal()
    procurarSomPedido = Signal()
    bindingEditado = Signal()

    def __init__(self, estado=None):
        super().__init__()
        self._gesture_buttons = []
        self._estado = estado
        self._atual = ""
        self._refletindo = False
        self._botoes_por_gesto = {}

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        root_layout.addWidget(self.scroll)

        content = QWidget()
        self.scroll.setWidget(content)

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
        self.hold_slider.setRange(5, 50)  # 0.5 a 5.0s (multiplicador de 0.1)
        self.hold_slider.setMinimumHeight(30)
        self.hold_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hold_value_spinbox = QDoubleSpinBox()
        self.hold_value_spinbox.setRange(0.5, 5.0)  # 0.5 a 5.0 segundos
        self.hold_value_spinbox.setSingleStep(1.0)  # Incremento de 1s com ↑↓ (mas permite digitar decimais)
        self.hold_value_spinbox.setDecimals(1)  # 1 casa decimal
        self.hold_value_spinbox.setSuffix("s")
        self.hold_value_spinbox.setMinimumWidth(80)
        self.hold_value_spinbox.setAlignment(Qt.AlignCenter)
        # Tooltip para indicar que é clicável
        self.hold_value_spinbox.setToolTip("Clique para editar ou use as setas (0.5-5.0s)")
        hold_row.addWidget(self.hold_slider)
        hold_row.addWidget(self.hold_value_spinbox)
        editor_layout.addLayout(hold_row)
        self.hold_time_note = QLabel("Recomendado: 2.0s para streaming ao vivo (protege contra gestos acidentais durante fala)")
        self.hold_time_note.setObjectName("muted")
        self.hold_time_note.setWordWrap(True)
        editor_layout.addWidget(self.hold_time_note)

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

        self.sound_file_error_label = QLabel()
        self.sound_file_error_label.setStyleSheet("color: #f44336; font-size: 12px;")
        self.sound_file_error_label.setVisible(False)
        editor_layout.addWidget(self.sound_file_error_label)
        self.sound_file_edit.editingFinished.connect(self._validate_sound_file)

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

        self._ligar_contrato()

    # ------------------------------------------------------------------ contrato

    def _ligar_contrato(self):
        self.choose_gestures_button.clicked.connect(self.escolherGestosPedido.emit)
        self.browse_sound_button.clicked.connect(self.procurarSomPedido.emit)

        for caixa, campo in (
            (self.scene_action_checkbox, "use_scene"),
            (self.sound_action_checkbox, "use_sound"),
            (self.hotkey_action_checkbox, "use_hotkey"),
        ):
            caixa.toggled.connect(lambda _=None: self._gravar_do_formulario())

        for editor in (self.scene_edit, self.sound_file_edit):
            editor.textEdited.connect(lambda _=None: self._gravar_do_formulario())

        self.hotkey_edit.hotkeyCommitted.connect(lambda _=None: self._gravar_do_formulario())
        self.hold_slider.valueChanged.connect(lambda _=None: self._gravar_do_formulario())
        self.cooldown_slider.valueChanged.connect(lambda _=None: self._gravar_do_formulario())

    def definir_gestos(self, entradas, selecionado):
        self.clear_gesture_grid()
        self._botoes_por_gesto = {}

        for indice, (nome, icone) in enumerate(entradas):
            botao = self.add_gesture_button(
                indice // 4, indice % 4, nome, lambda _=None, g=nome: self._escolher(g)
            )
            botao.setMinimumSize(110, 140)
            botao.setIconSize(QSize(64, 64))
            if icone and os.path.exists(icone):
                botao.setIcon(QIcon(icone))
            self._botoes_por_gesto[nome] = botao

        self._atual = selecionado or (entradas[0][0] if entradas else "")
        self._escolher(self._atual, avisar=False)

    def gesto_atual(self):
        return self._atual

    def _escolher(self, nome, avisar=True):
        if not nome:
            return
        self._atual = nome
        for chave, botao in self._botoes_por_gesto.items():
            botao.setChecked(chave == nome)
        self.refletir_binding()
        if avisar:
            self.gestoSelecionado.emit(nome)

    def refletir_binding(self):
        """Estado → formulário. `_refletindo` impede que isso pareça edição do usuário."""
        if self._estado is None or not self._atual:
            return

        cfg = self._estado.binding(self._atual)
        self._refletindo = True
        try:
            self.selected_gesture_label.setText(f"Gesto selecionado: {self._atual}")
            hold = max(0.5, min(5.0, float(cfg.get("hold_time", 2.0))))
            self.hold_value_spinbox.setValue(hold)
            self.hold_slider.setValue(int(hold * 10))

            cooldown = max(2.0, min(20.0, float(cfg.get("cooldown", 2.0))))
            self.cooldown_value_spinbox.setValue(cooldown)
            self.cooldown_slider.setValue(int(cooldown * 10))

            self.scene_action_checkbox.setChecked(bool(cfg.get("use_scene", False)))
            self.sound_action_checkbox.setChecked(bool(cfg.get("use_sound", False)))
            self.hotkey_action_checkbox.setChecked(bool(cfg.get("use_hotkey", False)))
            self.scene_edit.setText(cfg.get("scene", ""))
            self.sound_file_edit.setText(cfg.get("sound_file", ""))
            self.hotkey_edit.setText(cfg.get("hotkey", ""))
        finally:
            self._refletindo = False

        self.scene_edit.setEnabled(self.scene_action_checkbox.isChecked())
        self.sound_file_edit.setEnabled(self.sound_action_checkbox.isChecked())
        self.browse_sound_button.setEnabled(self.sound_action_checkbox.isChecked())
        self.hotkey_edit.setEnabled(self.hotkey_action_checkbox.isChecked())
        self._validate_sound_file()

    def _gravar_do_formulario(self):
        if self._refletindo or self._estado is None or not self._atual:
            return

        usa_som = self.sound_action_checkbox.isChecked()
        self._estado.definir_binding(
            self._atual,
            hold_time=self.hold_slider.value() / 10,
            cooldown=self.cooldown_slider.value() / 10,
            use_scene=self.scene_action_checkbox.isChecked(),
            use_sound=usa_som,
            play_sound=usa_som,
            use_hotkey=self.hotkey_action_checkbox.isChecked(),
            scene=self.scene_edit.text().strip(),
            sound_file=self.sound_file_edit.text().strip(),
            hotkey=self.hotkey_edit.text().strip(),
        )
        self.bindingEditado.emit()

    def definir_arquivo_de_som(self, caminho):
        self.sound_file_edit.setText(caminho)
        self._gravar_do_formulario()

    def _validate_sound_file(self):
        path = self.sound_file_edit.text().strip()
        if path and not os.path.isfile(path):
            self.sound_file_error_label.setText(f"Arquivo não encontrado: {path}")
            self.sound_file_error_label.setVisible(True)
        else:
            self.sound_file_error_label.setVisible(False)

    def clear_gesture_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Remove row/col constraints to prevent spacing issues
        for i in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowStretch(i, 0)
            self.grid_layout.setRowMinimumHeight(i, 0)
        
        self._gesture_buttons = []

    def add_gesture_button(self, row, col, text, callback):
        button = QToolButton()
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setObjectName("gestureBtn")
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        parts = text.split("\n", 1)
        emoji_text = parts[0] if parts else text
        button.setProperty("emojiText", emoji_text)
        button.setProperty("fullText", text)
        button.clicked.connect(callback)
        self.grid_layout.addWidget(button, row, col)
        self._gesture_buttons.append(button)
        self._refresh_gesture_button_texts()
        self._relayout_buttons()
        return button

    def _refresh_gesture_button_texts(self):
        for button in self._gesture_buttons:
            # We want to always show the full text (multiline) so things like "Dedo do Meio" are fully visible
            button.setText(button.property("fullText") or "")

    def _relayout_buttons(self):
        if not self._gesture_buttons or not hasattr(self, 'scroll'):
            return
        
        # calculate max columns based on scrollarea viewport width
        available_width = self.scroll.viewport().width() - 40 # some padding
        # minimum button width in main_window is ~110, plus layout spacing
        item_width = 120 
        col_count = max(1, available_width // item_width)
        
        for idx, button in enumerate(self._gesture_buttons):
            row = idx // col_count
            col = idx % col_count
            self.grid_layout.addWidget(button, row, col)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_gesture_button_texts()
        self._relayout_buttons()

    def showEvent(self, event):
        super().showEvent(event)
        # Call relayout when the tab is first shown, using a timer to let layouts calc geometry
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, self._relayout_buttons)
