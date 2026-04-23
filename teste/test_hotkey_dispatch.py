import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from actions.action_manager import ActionManager


class FakeKeyboard:
    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))


def run_tests():
    manager = ActionManager(None)

    # Testa normalizacao no padrao OBS: Ctrl + Alt + Shift + tecla
    assert manager._normalizar_atalho_para_keyboard("Shift+Ctrl+Alt+F") == "ctrl+alt+shift+f"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+F") == "ctrl+shift+f"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Plus") == "ctrl+shift++"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+PageUp") == "ctrl+page up"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+PgDown") == "ctrl+page down"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Delete") == "ctrl+delete"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+F12") == "ctrl+f12"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+/") == "ctrl+/"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Z") == "ctrl+shift+z"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+A") == "ctrl+shift+a"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Q") == "ctrl+shift+q"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+W") == "ctrl+shift+w"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+E") == "ctrl+shift+e"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Alt+Z") == "ctrl+alt+shift+z"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Alt+A") == "ctrl+alt+shift+a"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Alt+Q") == "ctrl+alt+shift+q"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Alt+W") == "ctrl+alt+shift+w"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Shift+Alt+E") == "ctrl+alt+shift+e"
    assert manager._normalizar_atalho_para_keyboard("Ctrl+Alt") is None

    # Testa mapeamento de VK (caminho SendInput)
    assert manager._token_to_vk("a") == 0x41
    assert manager._token_to_vk("z") == 0x5A
    assert manager._token_to_vk("0") == 0x30
    assert manager._token_to_vk("9") == 0x39
    assert manager._token_to_vk("f12") == 0x7B
    assert manager._token_to_vk("page up") == 0x21
    assert manager._token_to_vk("/") == 0xBF

    # Testa fallback da lib keyboard forçando SendInput indisponível
    manager._sendinput_available = False
    fake = FakeKeyboard()
    import actions.action_manager as am
    real_keyboard = am.keyboard
    am.keyboard = fake
    try:
        manager._enviar_atalho("ctrl+alt+shift+f")
    finally:
        am.keyboard = real_keyboard

    expected_prefix = [
        ("release", "left ctrl"),
        ("release", "left alt"),
        ("release", "left shift"),
        ("release", "left windows"),
        ("press", "left ctrl"),
        ("press", "left alt"),
        ("press", "left shift"),
        ("press", "f"),
        ("release", "f"),
    ]
    assert fake.events[:9] == expected_prefix, fake.events
    assert fake.events[-3:] == [
        ("release", "left shift"),
        ("release", "left alt"),
        ("release", "left ctrl"),
    ], fake.events

    print("OK: testes de hotkey passaram")


if __name__ == "__main__":
    run_tests()
