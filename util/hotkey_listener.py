import keyboard
from typing import Callable, Optional
import ctypes


class HotkeyListener:
    
    def __init__(self):
        self._listening = False
        self._pressed_keys = set()  # Todas as teclas pressionadas
        self._callback = None
        self._on_cancel_callback = None
        self._modifier_names = {
            'ctrl': 'Ctrl',
            'control': 'Ctrl',
            'shift': 'Shift',
            'alt': 'Alt',
            'cmd': 'Win',
            'windows': 'Win',
            'meta': 'Win',
            'win': 'Win',
            'left ctrl': 'Ctrl',
            'right ctrl': 'Ctrl',
            'left shift': 'Shift',
            'right shift': 'Shift',
            'left alt': 'Alt',
            'right alt': 'Alt',
            'alt gr': 'Alt',
            'altgr': 'Alt',
            'left windows': 'Win',
            'right windows': 'Win'
        }
        self._modifier_order = ['ctrl', 'alt', 'shift', 'win']
        self._user32 = None
        try:
            self._user32 = ctypes.WinDLL('user32', use_last_error=True)
        except Exception:
            self._user32 = None
    
    def start_listening(self, callback: Callable[[str], None], on_cancel: Optional[Callable[[], None]] = None):
        """
        Inicia a escuta de teclado (modo dual - sequencial ou tudo junto).
        
        Funciona de duas formas:
        1. Sequencial: Ctrl → Shift → C
        2. Junto: Ctrl+Shift+C (mantendo tudo pressionado)
        
        Args:
            callback: Função que será chamada com a combinação de teclas (ex: "Ctrl+Shift+M")
            on_cancel: Função chamada se o usuário pressionar ESC
        """
        if self._listening:
            return
        
        self._listening = True
        self._pressed_keys = set()
        self._callback = callback
        self._on_cancel_callback = on_cancel
        
        # Remove listeners anteriores
        try:
            keyboard.unhook_all()
        except:
            pass
        
        def on_press(event):
            if not self._listening:
                return
            try:
                key_name = self._normalize_key_name(getattr(event, 'name', None))
                if key_name:
                    self._pressed_keys.add(key_name)
            except:
                pass
        
        def on_release(event):
            if not self._listening:
                return
            
            try:
                key_name = self._normalize_key_name(getattr(event, 'name', None))
                
                # Se pressionar ESC, cancela
                if key_name == 'esc':
                    self._listening = False
                    try:
                        keyboard.unhook_all()
                    except:
                        pass
                    if self._on_cancel_callback:
                        self._on_cancel_callback()
                    return
                
                # Se uma tecla normal foi liberada (não é modificador)
                if key_name not in self._modifier_names:
                    # Pega todos os modificadores ainda pressionados (ordem determinística)
                    modifiers = []
                    for mod_key in self._modifier_order:
                        if mod_key in self._pressed_keys:
                            pretty = self._modifier_names.get(mod_key)
                            if pretty and pretty not in modifiers:
                                modifiers.append(pretty)
                    
                    if modifiers:
                        # Tem modificadores, pode capturar
                        self._listening = False
                        try:
                            keyboard.unhook_all()
                        except:
                            pass
                        
                        # Formata a tecla
                        formatted_key = self._format_non_modifier_key(event)
                        if not formatted_key:
                            return
                        modifiers.append(formatted_key)
                        hotkey_str = '+'.join(modifiers)
                        
                        if self._callback:
                            self._callback(hotkey_str)
                        return
                
                # Remove a tecla que foi solta (após processar)
                self._pressed_keys.discard(key_name)
            except:
                pass
        
        # Registra os listeners
        try:
            keyboard.on_press(on_press)
            keyboard.on_release(on_release)
        except Exception as e:
            print(f"Erro ao registrar listeners: {e}")
            self._listening = False
    
    def stop_listening(self):
        """Para a escuta de teclado."""
        self._listening = False
        self._pressed_keys.clear()
        self._callback = None
        self._on_cancel_callback = None
        try:
            keyboard.unhook_all()
        except:
            pass
    
    def is_listening(self) -> bool:
        """Retorna se está escutando."""
        return self._listening

    def _normalize_key_name(self, key_name):
        if key_name is None:
            return ""
        try:
            return str(key_name).strip().lower()
        except Exception:
            return ""

    def _format_non_modifier_key(self, event):
        key_name = self._normalize_key_name(getattr(event, 'name', None))
        if not key_name:
            return ""

        mapped = {
            'space': 'Space',
            'tab': 'Tab',
            'enter': 'Enter',
            'return': 'Enter',
            'backspace': 'Backspace',
            'delete': 'Delete',
            'insert': 'Insert',
            'home': 'Home',
            'end': 'End',
            'page up': 'PageUp',
            'page down': 'PageDown',
            'up': 'Up',
            'down': 'Down',
            'left': 'Left',
            'right': 'Right',
            'esc': 'Esc',
            'escape': 'Esc',
        }
        if key_name in mapped:
            return mapped[key_name]

        if key_name.startswith('f') and key_name[1:].isdigit():
            try:
                fn = int(key_name[1:])
                if 1 <= fn <= 24:
                    return f'F{fn}'
            except Exception:
                pass

        if len(key_name) == 1:
            if key_name.isascii():
                return key_name.upper()

            scan_code = getattr(event, 'scan_code', None)
            fallback = self._scan_code_to_key_name(scan_code)
            if fallback:
                return fallback

            return ""

        return ""

    def _scan_code_to_key_name(self, scan_code):
        if self._user32 is None:
            return ""
        if scan_code is None:
            return ""

        try:
            scan = int(scan_code)
        except Exception:
            return ""

        MAPVK_VSC_TO_VK_EX = 3
        try:
            vk = int(self._user32.MapVirtualKeyW(scan, MAPVK_VSC_TO_VK_EX))
        except Exception:
            return ""

        if 0x41 <= vk <= 0x5A:
            return chr(vk)
        if 0x30 <= vk <= 0x39:
            return chr(vk)
        if 0x70 <= vk <= 0x87:
            return f'F{vk - 0x6F}'
        return ""
