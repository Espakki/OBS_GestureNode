import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from ui.tabs.gestos_tab import HotkeyLineEdit


def run_tests():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    def capture_combo(final_key, final_text, expected, with_alt=False):
        field = HotkeyLineEdit()
        field._start_capture()

        mods = Qt.ControlModifier | Qt.ShiftModifier
        field.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Control, Qt.ControlModifier, ""))
        if with_alt:
            mods |= Qt.AltModifier
            field.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Alt, Qt.ControlModifier | Qt.AltModifier, ""))
        field.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Shift, mods, ""))

        field.keyPressEvent(QKeyEvent(QEvent.KeyPress, final_key, mods, final_text))
        assert field.text() == expected, field.text()

    capture_combo(Qt.Key_F, "f", "Ctrl+Shift+F")
    capture_combo(Qt.Key_Z, "z", "Ctrl+Shift+Z")
    capture_combo(Qt.Key_A, "a", "Ctrl+Shift+A")
    capture_combo(Qt.Key_Q, "q", "Ctrl+Shift+Q")
    capture_combo(Qt.Key_W, "w", "Ctrl+Shift+W")
    capture_combo(Qt.Key_E, "e", "Ctrl+Shift+E")
    capture_combo(Qt.Key_Z, "z", "Ctrl+Alt+Shift+Z", with_alt=True)
    capture_combo(Qt.Key_Z, "æ", "Ctrl+Alt+Shift+Z", with_alt=True)
    capture_combo(Qt.Key_A, "a", "Ctrl+Alt+Shift+A", with_alt=True)
    capture_combo(Qt.Key_Q, "q", "Ctrl+Alt+Shift+Q", with_alt=True)
    capture_combo(Qt.Key_W, "w", "Ctrl+Alt+Shift+W", with_alt=True)
    capture_combo(Qt.Key_E, "e", "Ctrl+Alt+Shift+E", with_alt=True)
    capture_combo(Qt.Key_F, "f", "Ctrl+Alt+Shift+F", with_alt=True)

    print("OK: captura Ctrl+Shift+Z/A/Q/W/E e Ctrl+Alt+Shift+Z/A/Q/W/E/F")

    app.quit()


if __name__ == "__main__":
    run_tests()
