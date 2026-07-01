APP_STYLESHEET = """
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
