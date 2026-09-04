"""Implementação de fallback, sem API nativa de nenhum sistema. Ver D-42.

Serve para dois casos: sistema ainda sem implementação própria, e fallback do Windows
quando o `SendInput` falha. Por isso vive num módulo separado em vez de dentro de
`_windows.py` — o futuro `_linux.py` vai querer o mesmo fallback de teclado.

O pacote `keyboard` funciona nos dois sistemas, mas **exige root no Linux**, então aqui
ele é rede de segurança, não a estratégia principal.
"""

import time

try:
    import keyboard
except Exception:
    keyboard = None

from util.logger import get_logger

logger = get_logger(__name__)

NOME = "genérico"

# FFmpeg no Linux; é o palpite mais útil para um sistema sem implementação própria.
FORMATO_CAPTURA = "v4l2"


def url_do_dispositivo(nome_dispositivo, indice=0):
    return f"/dev/video{int(indice)}"


def tocar_som(caminho):
    logger.warning(
        "Reprodução de áudio não implementada nesta plataforma; som ignorado: %s", caminho
    )
    return False


def enviar_atalho(mods, tecla):
    """Envia a combinação usando o pacote `keyboard`.

    Solta os modificadores antes de começar: em tempo real, um modificador preso de um
    disparo anterior fazia a combinação seguinte sair errada.
    """
    if keyboard is None:
        logger.warning("Pacote `keyboard` indisponível; atalho não enviado")
        return False

    mod_para_esquerdo = {
        "ctrl": "left ctrl",
        "alt": "left alt",
        "shift": "left shift",
        "windows": "left windows",
    }

    for mod in ("left ctrl", "left alt", "left shift", "left windows"):
        try:
            keyboard.release(mod)
        except Exception:
            pass
    time.sleep(0.01)

    pressionados = []
    try:
        for mod in mods:
            esquerdo = mod_para_esquerdo.get(mod, mod)
            keyboard.press(esquerdo)
            pressionados.append(esquerdo)
            time.sleep(0.02)

        keyboard.press(tecla)
        time.sleep(0.03)
        keyboard.release(tecla)
        return True
    except Exception as exc:
        logger.exception("Falha ao enviar atalho pelo pacote keyboard: %s", exc)
        return False
    finally:
        for mod in reversed(pressionados):
            try:
                keyboard.release(mod)
                time.sleep(0.02)
            except Exception:
                pass
