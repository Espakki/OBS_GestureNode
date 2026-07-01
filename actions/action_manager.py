import os
import platform
import time
import winsound
import ctypes

try:
    import keyboard
except Exception:
    keyboard = None

from util.logger import get_logger


logger = get_logger(__name__)


KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INPUT_KEYBOARD = 1
MAPVK_VK_TO_VSC = 0


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint),
        ("ki", KEYBDINPUT),
    ]


class ActionManager:
    def __init__(self, obs_controller, modo="automatico"):
        self.obs = obs_controller
        self.modo = str(modo or "automatico").lower()
        self._sendinput_available = False
        self._user32 = None
        if platform.system().lower() == "windows":
            try:
                self._user32 = ctypes.WinDLL("user32", use_last_error=True)
                self._sendinput_available = True
            except Exception:
                self._sendinput_available = False

    def executar(self, tipo, valor=None):
        if self.modo == "teste":
            logger.info("Ação bloqueada pelo Modo Teste: tipo=%s valor=%s", tipo, valor)
            return

        if tipo == "trocar_cena":
            if self.obs and self.obs.connected:
                self.obs.trocar_cena(valor)
            else:
                logger.warning("OBS não conectado para trocar cena")

        elif tipo == "iniciar_live":
            if self.obs and self.obs.connected and self.obs.cliente:
                self.obs.cliente.start_stream()

        elif tipo == "parar_live":
            if self.obs and self.obs.connected and self.obs.cliente:
                self.obs.cliente.stop_stream()

        elif tipo == "tocar_som":
            self._tocar_som(valor)

        elif tipo == "atalho":
            self._acionar_atalho(valor)

        else:
            logger.warning("Ação desconhecida: %s", tipo)

    def _tocar_som(self, caminho):
        if not caminho:
            return

        if not os.path.exists(caminho):
            logger.warning("Arquivo de som não encontrado: %s", caminho)
            return

        if platform.system().lower() == "windows":
            try:
                winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as exc:
                logger.exception("Falha ao tocar som: %s", exc)
        else:
            logger.warning("Reprodução de som suportada apenas no Windows nesta versão")

    def _acionar_atalho(self, hotkey_texto):
        if not hotkey_texto:
            return

        if not self._sendinput_available and keyboard is None:
            logger.warning("Sem backend de teclado disponível (SendInput/keyboard)")
            return

        try:
            atalho = self._normalizar_atalho_para_keyboard(hotkey_texto)
            if not atalho:
                logger.warning("Atalho inválido ignorado: '%s'", hotkey_texto)
                return
            self._enviar_atalho(atalho)
            logger.info("Atalho enviado: %s", atalho)
        except Exception as exc:
            logger.exception("Falha ao acionar atalho '%s': %s", hotkey_texto, exc)

    def _normalizar_atalho_para_keyboard(self, hotkey_texto):
        """Converte texto da UI para formato aceito pelo pacote keyboard."""
        partes = [p.strip() for p in str(hotkey_texto).split("+") if p.strip()]
        if len(partes) < 2:
            return None

        mod_map = {
            "ctrl": "ctrl",
            "control": "ctrl",
            "shift": "shift",
            "alt": "alt",
            "win": "windows",
            "meta": "windows",
            "windows": "windows",
        }

        key_map = {
            "return": "enter",
            "enter": "enter",
            "escape": "esc",
            "esc": "esc",
            "space": "space",
            "tab": "tab",
            "menu": "menu",
            "help": "help",
            "pause": "pause",
            "printscreen": "print screen",
            "print": "print screen",
            "scrolllock": "scroll lock",
            "capslock": "caps lock",
            "numlock": "num lock",
            "backspace": "backspace",
            "delete": "delete",
            "insert": "insert",
            "home": "home",
            "end": "end",
            "pageup": "page up",
            "page_up": "page up",
            "pgup": "page up",
            "pagedown": "page down",
            "page_down": "page down",
            "pgdown": "page down",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "plus": "+",
        }

        mods = []
        key_part = None
        for parte in partes:
            token = parte.lower()
            if token in mod_map:
                mapped = mod_map[token]
                if mapped not in mods:
                    mods.append(mapped)
            else:
                key_part = key_map.get(token, token)

        if key_part and key_part.startswith("f") and key_part[1:].isdigit():
            key_part = key_part.lower()

        # Protege contra envio incompleto tipo "ctrl+shift" sem tecla final.
        if not mods or not key_part:
            return None

        # Ordem determinística ajuda debug e evita variações entre capturas.
        ordem = ["ctrl", "alt", "shift", "windows"]
        mods_ordenados = [m for m in ordem if m in mods]
        return "+".join(mods_ordenados + [key_part])

    def _enviar_atalho(self, atalho):
        """Envia o atalho com sequência determinística (left modifiers)."""
        partes = atalho.split("+")
        if len(partes) < 2:
            return

        mods = partes[:-1]
        tecla = partes[-1]

        if tecla in {"ctrl", "shift", "alt", "windows"}:
            return

        if self._sendinput_available and self._user32 is not None:
            ok = self._enviar_atalho_sendinput(mods, tecla)
            if ok:
                return

        self._enviar_atalho_keyboard_fallback(mods, tecla)

    def _enviar_atalho_keyboard_fallback(self, mods, tecla):
        """Fallback usando lib keyboard quando SendInput não estiver disponível."""
        if keyboard is None:
            return

        mod_to_left = {
            "ctrl": "left ctrl",
            "alt": "left alt",
            "shift": "left shift",
            "windows": "left windows",
        }

        # Estado limpo antes do disparo melhora confiabilidade em tempo real.
        for mod in ("left ctrl", "left alt", "left shift", "left windows"):
            try:
                keyboard.release(mod)
            except Exception:
                pass
        time.sleep(0.01)

        pressed = []
        for mod in mods:
            left_mod = mod_to_left.get(mod, mod)
            keyboard.press(left_mod)
            pressed.append(left_mod)
            time.sleep(0.02)

        try:
            keyboard.press(tecla)
            time.sleep(0.03)
            keyboard.release(tecla)
        finally:
            for mod in reversed(pressed):
                keyboard.release(mod)
                time.sleep(0.02)

    def _enviar_atalho_sendinput(self, mods, tecla):
        """Envio nativo Win32 via SendInput (mais confiável para OBS)."""
        vk_mod_map = {
            "ctrl": 0xA2,   # VK_LCONTROL
            "alt": 0xA4,    # VK_LMENU
            "shift": 0xA0,  # VK_LSHIFT
            "windows": 0x5B,  # VK_LWIN
        }

        key_vk = self._token_to_vk(tecla)
        if key_vk is None:
            return False

        pressed_mods = []
        try:
            for mod in mods:
                vk = vk_mod_map.get(mod)
                if vk is None:
                    continue
                if not self._send_key_by_scancode(vk, keyup=False, prefer_scancode=True):
                    logger.warning("SendInput falhou ao pressionar modificador VK=%s", hex(vk))
                    return False
                pressed_mods.append(vk)
                time.sleep(0.01)

            if not self._send_key_by_scancode(key_vk, keyup=False, prefer_scancode=True):
                logger.warning("SendInput falhou ao pressionar tecla VK=%s", hex(key_vk))
                return False
            time.sleep(0.02)
            if not self._send_key_by_scancode(key_vk, keyup=True, prefer_scancode=True):
                logger.warning("SendInput falhou ao soltar tecla VK=%s", hex(key_vk))
                return False
            return True
        except Exception:
            return False
        finally:
            for vk in reversed(pressed_mods):
                try:
                    self._send_key_by_scancode(vk, keyup=True, prefer_scancode=True)
                    time.sleep(0.01)
                except Exception:
                    pass

    def _token_to_vk(self, token):
        token = str(token or "").lower().strip()
        if not token:
            return None

        if len(token) == 1 and token.isalpha():
            return ord(token.upper())

        if len(token) == 1 and token.isdigit():
            return ord(token)

        if token.startswith("f") and token[1:].isdigit():
            fn = int(token[1:])
            if 1 <= fn <= 24:
                return 0x70 + (fn - 1)  # VK_F1..VK_F24

        vk_map = {
            "enter": 0x0D,
            "tab": 0x09,
            "space": 0x20,
            "esc": 0x1B,
            "backspace": 0x08,
            "delete": 0x2E,
            "insert": 0x2D,
            "home": 0x24,
            "end": 0x23,
            "page up": 0x21,
            "page down": 0x22,
            "up": 0x26,
            "down": 0x28,
            "left": 0x25,
            "right": 0x27,
            "/": 0xBF,
            "\\": 0xDC,
            ",": 0xBC,
            ".": 0xBE,
            ";": 0xBA,
            "'": 0xDE,
            "[": 0xDB,
            "]": 0xDD,
            "`": 0xC0,
            "-": 0xBD,
            "=": 0xBB,
            "+": 0xBB,
        }
        return vk_map.get(token)

    def _send_vk(self, vk, keyup=False):
        flags = KEYEVENTF_KEYUP if keyup else 0
        ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
        inp = INPUT(type=INPUT_KEYBOARD, ki=ki)
        sent = self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        return bool(sent == 1)

    def _send_key_by_scancode(self, vk, keyup=False, prefer_scancode=True):
        if self._user32 is None:
            return False

        if not prefer_scancode:
            return self._send_vk(vk, keyup=keyup)

        scan = self._user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
        if not scan:
            return self._send_vk(vk, keyup=keyup)

        flags = KEYEVENTF_SCANCODE
        if keyup:
            flags |= KEYEVENTF_KEYUP

        # Algumas teclas precisam da flag extended no caminho de scan code.
        if vk in {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B}:
            flags |= KEYEVENTF_EXTENDEDKEY

        ki = KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
        inp = INPUT(type=INPUT_KEYBOARD, ki=ki)
        sent = self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        return bool(sent == 1)