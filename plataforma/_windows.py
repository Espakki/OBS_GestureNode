"""Implementação Windows: `winsound` para áudio, `SendInput` para teclas. Ver D-42.

Este módulo **só é importado no Windows** (ver `plataforma/__init__.py`). É por isso que
ele pode fazer `import winsound` no topo sem quebrar Linux: em Linux ninguém o importa.

O código veio de `actions/action_manager.py` sem mudança de comportamento — o B-22 foi
mover, não reescrever. Os testes existentes cobrem o que ficou lá em cima (parsing e
validação); o que está aqui só se prova com Windows real.
"""

import ctypes
import os
import time
import winsound

from plataforma import _generico
from util.logger import get_logger

logger = get_logger(__name__)

NOME = "Windows"

FORMATO_CAPTURA = "dshow"

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INPUT_KEYBOARD = 1
MAPVK_VK_TO_VSC = 0

# VK dos modificadores. Sempre os da ESQUERDA: o OBS distingue, e misturar left/right
# fazia o atalho registrado não bater com o enviado.
VK_MODIFICADORES = {
    "ctrl": 0xA2,  # VK_LCONTROL
    "alt": 0xA4,  # VK_LMENU
    "shift": 0xA0,  # VK_LSHIFT
    "windows": 0x5B,  # VK_LWIN
}

# Teclas que exigem a flag extended no caminho de scan code.
VK_ESTENDIDAS = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B}

VK_NOMEADAS = {
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


def _carregar_user32():
    try:
        return ctypes.WinDLL("user32", use_last_error=True)
    except Exception as exc:
        logger.warning("user32 indisponível; SendInput desativado: %s", exc)
        return None


_user32 = _carregar_user32()


def url_do_dispositivo(nome_dispositivo, indice=0):
    """DirectShow endereça por NOME, não por índice — daí o `video=`."""
    return f"video={nome_dispositivo}"


def tocar_som(caminho):
    if not caminho:
        return False

    if not os.path.exists(caminho):
        logger.warning("Arquivo de som não encontrado: %s", caminho)
        return False

    try:
        winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    except Exception as exc:
        logger.exception("Falha ao tocar som: %s", exc)
        return False


def token_para_vk(token):
    """Converte um nome de tecla no virtual-key code do Windows."""
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

    return VK_NOMEADAS.get(token)


def _enviar_vk(vk, soltar=False):
    flags = KEYEVENTF_KEYUP if soltar else 0
    ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
    inp = INPUT(type=INPUT_KEYBOARD, ki=ki)
    return bool(_user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) == 1)


def _enviar_por_scancode(vk, soltar=False):
    """Prefere scan code: é o que jogos e o OBS costumam escutar.

    Sem scan code disponível para a tecla, cai para o envio por virtual-key.
    """
    if _user32 is None:
        return False

    scan = _user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
    if not scan:
        return _enviar_vk(vk, soltar=soltar)

    flags = KEYEVENTF_SCANCODE
    if soltar:
        flags |= KEYEVENTF_KEYUP
    if vk in VK_ESTENDIDAS:
        flags |= KEYEVENTF_EXTENDEDKEY

    ki = KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
    inp = INPUT(type=INPUT_KEYBOARD, ki=ki)
    return bool(_user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) == 1)


def _enviar_por_sendinput(mods, tecla):
    vk_tecla = token_para_vk(tecla)
    if vk_tecla is None:
        return False

    pressionados = []
    try:
        for mod in mods:
            vk = VK_MODIFICADORES.get(mod)
            if vk is None:
                continue
            if not _enviar_por_scancode(vk, soltar=False):
                logger.warning("SendInput falhou no modificador VK=%s", hex(vk))
                return False
            pressionados.append(vk)
            time.sleep(0.01)

        if not _enviar_por_scancode(vk_tecla, soltar=False):
            logger.warning("SendInput falhou ao pressionar VK=%s", hex(vk_tecla))
            return False
        time.sleep(0.02)
        if not _enviar_por_scancode(vk_tecla, soltar=True):
            logger.warning("SendInput falhou ao soltar VK=%s", hex(vk_tecla))
            return False
        return True
    except Exception:
        return False
    finally:
        for vk in reversed(pressionados):
            try:
                _enviar_por_scancode(vk, soltar=True)
                time.sleep(0.01)
            except Exception:
                pass


def enviar_atalho(mods, tecla):
    """SendInput primeiro; o pacote `keyboard` como rede.

    SendInput é mais confiável com o OBS, mas depende do `user32` ter carregado e da
    tecla ter virtual-key conhecido. Quando qualquer um falha, o backend genérico ainda
    tenta — melhor um caminho menos confiável que nenhum.
    """
    if _user32 is not None and _enviar_por_sendinput(mods, tecla):
        return True

    return _generico.enviar_atalho(mods, tecla)
