#!/usr/bin/env python3
"""Script de teste para debugar a captura de hotkeys."""

import keyboard
import sys
from util.hotkey_listener import HotkeyListener

def test_hotkey_capture():
    """Testa a captura de hotkeys."""
    listener = HotkeyListener()
    
    def on_hotkey(hotkey):
        print(f"✓ Hotkey capturado: {hotkey}")
        sys.exit(0)
    
    def on_cancel():
        print("✗ Captura cancelada (ESC)")
        sys.exit(0)
    
    print("Iniciando teste de captura de hotkeys...")
    print("Pressione uma combinação (ex: Ctrl+Shift+C)")
    print("Ou pressione ESC para cancelar")
    print()
    
    listener.start_listening(callback=on_hotkey, on_cancel=on_cancel)
    
    # Aguarda
    try:
        import time
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")
        listener.stop_listening()

if __name__ == "__main__":
    test_hotkey_capture()
