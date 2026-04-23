import keyboard
from typing import Callable, Optional


class HotkeyListener:
    """Utilitário para capturar combinações de teclas do teclado (estilo OBS - dual mode)."""
    
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
            'win': 'Win'
        }
    
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
                self._pressed_keys.add(event.name.lower())
            except:
                pass
        
        def on_release(event):
            if not self._listening:
                return
            
            try:
                key_name = event.name.lower()
                
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
                    # Pega todos os modificadores ainda pressionados
                    modifiers = [self._modifier_names[k] for k in self._pressed_keys 
                                if k in self._modifier_names]
                    
                    if modifiers:
                        # Tem modificadores, pode capturar
                        self._listening = False
                        try:
                            keyboard.unhook_all()
                        except:
                            pass
                        
                        modifiers.sort()
                        # Formata a tecla
                        formatted_key = event.name.upper() if len(event.name) == 1 else event.name.capitalize()
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
