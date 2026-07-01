APP_STYLESHEET = """
/* === Streamer Dark — base === */
QMainWindow, QDialog, QWidget {
    background-color: #0d0d0d;
    color: #f0f0f0;
    font-size: 15px;
}
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* === Tabs === */
QTabWidget::pane { border: 1px solid #2d2d2d; background: #161616; }
QTabBar::tab {
    background: #1a1a1a;
    min-width: 92px;
    padding: 10px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 15px;
    color: #707070;
}
QTabBar::tab:selected { background: #161616; color: #f0f0f0; border-bottom: 2px solid #7c4dff; }
QTabBar::tab:hover:!selected { background: #222222; color: #b0b0b0; }

/* === Cards / Panels === */
QFrame#card { background: #161616; border: 1px solid #2d2d2d; border-radius: 10px; }
QFrame#bottomPanel { background: #161616; border: 1px solid #2d2d2d; border-radius: 8px; }
QWidget#transparentRow { background: transparent; }

/* === Labels === */
QLabel { font-size: 15px; background: transparent; }
QLabel#sectionTitle { color: #c0b0ff; font-size: 17px; font-weight: 700; background: transparent; }
QLabel#muted { color: #707070; font-size: 14px; background: transparent; }
QLabel#healthLabel { color: #a0a0a0; font-size: 14px; background: transparent; }
QLabel#title { color: #9d6fff; font-size: 22px; font-weight: 800; background: transparent; }

/* === Checkboxes === */
QCheckBox { spacing: 8px; font-size: 15px; background: transparent; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #2d2d2d;
    border-radius: 3px;
    background: #1e1e1e;
}
QCheckBox::indicator:hover { border-color: #7c4dff; }
QCheckBox::indicator:checked {
    background: #7c4dff;
    border-color: #7c4dff;
    image: none;
}
QRadioButton { spacing: 8px; font-size: 15px; background: transparent; }

/* === Inputs === */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 5px;
    color: #f0f0f0;
    min-height: 20px;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: #404040; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #7c4dff; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background: #111111;
    border: 1px solid #1e1e1e;
    color: #404040;
}

QComboBox {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 5px;
    color: #f0f0f0;
    min-height: 20px;
}
QComboBox:hover { border-color: #404040; }
QComboBox:focus { border: 1px solid #7c4dff; }
QComboBox:disabled { background: #111111; border: 1px solid #1e1e1e; color: #404040; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    selection-background-color: #7c4dff;
    selection-color: #ffffff;
    color: #f0f0f0;
    outline: none;
}

/* === Sliders === */
QSlider { background: transparent; }
QSlider::groove:horizontal { height: 10px; background: #2a2a2a; border-radius: 5px; margin: 6px 0; }
QSlider::handle:horizontal {
    background: #7c4dff;
    width: 20px;
    margin: -6px 0;
    border-radius: 10px;
}
QSlider::handle:horizontal:hover { background: #9965ff; }
QSlider::sub-page:horizontal { background: #7c4dff; border-radius: 5px; }

/* === Buttons — base === */
QPushButton, QToolButton {
    background: #2a2a2a;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    color: #f0f0f0;
    font-weight: 600;
    font-size: 15px;
    outline: none;
}
QPushButton:hover, QToolButton:hover { background: #3a3a3a; }
QPushButton:pressed, QToolButton:pressed { background: #222222; }
QPushButton:focus, QToolButton:focus { outline: none; }
QPushButton:disabled, QToolButton:disabled { background: #1a1a1a; color: #404040; }

/* === Primary (Iniciar) === */
QPushButton#primary { background: #7c4dff; color: #ffffff; }
QPushButton#primary:hover { background: #9965ff; }
QPushButton#primary:pressed { background: #6a3de0; }
QPushButton#primary:disabled { background: #3a2a6a; color: #7060a0; }

/* === Danger / Warning === */
QPushButton#danger { background: #c0392b; color: #ffffff; }
QPushButton#danger:hover { background: #e74c3c; }
QPushButton#danger:pressed { background: #a93226; }
QPushButton#warning { background: #b7770d; color: #ffffff; }
QPushButton#warning:hover { background: #d68910; }
QPushButton#warning:pressed { background: #9a6209; }

/* === Ghost toggle (Configurações Avançadas) === */
QPushButton#ghost {
    background: #1e1e1e;
    color: #707070;
    border: 1px solid #2d2d2d;
}
QPushButton#ghost:hover { background: #252525; color: #b0b0b0; border-color: #3d3d3d; }
QPushButton#ghost:checked { color: #f0f0f0; border-color: #7c4dff; }

/* === Option toggles (Resolução / FPS / Modo / Mãos) === */
QPushButton#optionToggle {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    color: #909090;
}
QPushButton#optionToggle:hover { background: #252525; border-color: #404040; color: #f0f0f0; }
QPushButton#optionToggle:pressed { background: #181818; }
QPushButton#optionToggle:focus { border: 1px solid #2d2d2d; outline: none; }
QPushButton#optionToggle:checked { background: #7c4dff; border: 1px solid #7c4dff; color: #ffffff; }
QPushButton#optionToggle:checked:hover { background: #9965ff; border-color: #9965ff; }
QPushButton#optionToggle:checked:pressed { background: #6a3de0; border-color: #6a3de0; }
QPushButton#optionToggle:disabled { background: #141414; border-color: #1e1e1e; color: #404040; }

/* === Gesture grid buttons === */
QPushButton#gestureBtn, QToolButton#gestureBtn {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    padding: 15px;
    max-height: 150px;
    color: #909090;
}
QPushButton#gestureBtn:hover, QToolButton#gestureBtn:hover {
    background: #252525;
    border-color: #404040;
    color: #f0f0f0;
}
QPushButton#gestureBtn:checked, QToolButton#gestureBtn:checked {
    border: 2px solid #7c4dff;
    background: #1b1428;
    color: #f0f0f0;
}

/* === Gesture selector buttons === */
QPushButton#gestureSelect, QToolButton#gestureSelect {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    min-height: 64px;
    padding: 8px;
    color: #909090;
}
QPushButton#gestureSelect:hover, QToolButton#gestureSelect:hover {
    background: #252525;
    border-color: #404040;
    color: #f0f0f0;
}
QPushButton#gestureSelect:pressed, QToolButton#gestureSelect:pressed { background: #181818; }
QPushButton#gestureSelect:focus, QToolButton#gestureSelect:focus { border: 1px solid #2d2d2d; }
QPushButton#gestureSelect:checked, QToolButton#gestureSelect:checked {
    border: 2px solid #7c4dff;
    background: #1b1428;
    color: #f0f0f0;
}
QPushButton#gestureSelect:checked:hover, QToolButton#gestureSelect:checked:hover {
    background: #231a35;
}
QPushButton#gestureSelect:checked:pressed, QToolButton#gestureSelect:checked:pressed {
    background: #150f20;
}

/* === Log === */
QPlainTextEdit {
    background: #0a0a0a;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    color: #909090;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background: #111111;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2d2d2d;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #7c4dff; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal {
    background: #111111;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2d2d2d;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #7c4dff; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

DARK_STYLESHEET = APP_STYLESHEET
