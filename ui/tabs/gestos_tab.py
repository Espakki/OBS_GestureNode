from PySide6.QtCore import Qt
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
    QVBoxLayout,
    QWidget,
)


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
        self.hold_slider.setRange(1, 50)
        self.hold_slider.setMinimumHeight(30)
        self.hold_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hold_value_label = QLabel("0.0s")
        self.hold_value_label.setMinimumWidth(52)
        self.hold_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hold_row.addWidget(self.hold_slider)
        hold_row.addWidget(self.hold_value_label)
        editor_layout.addLayout(hold_row)

        cooldown_row = QHBoxLayout()
        cooldown_row.setSpacing(10)
        cooldown_label = QLabel("Cooldown:")
        cooldown_label.setMinimumWidth(140)
        cooldown_row.addWidget(cooldown_label)
        self.cooldown_slider = QSlider(Qt.Horizontal)
        self.cooldown_slider.setRange(0, 200)
        self.cooldown_slider.setMinimumHeight(30)
        self.cooldown_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cooldown_value_label = QLabel("0.0s")
        self.cooldown_value_label.setMinimumWidth(52)
        self.cooldown_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cooldown_row.addWidget(self.cooldown_slider)
        cooldown_row.addWidget(self.cooldown_value_label)
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
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("Ex: Ctrl+Shift+M")
        self.hotkey_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hotkey_row_layout.addWidget(self.hotkey_edit)
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
