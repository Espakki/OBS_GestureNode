import plataforma
from util.logger import get_logger


logger = get_logger(__name__)




class ActionManager:
    """Executa as ações de um gesto. Não sabe em que sistema operacional está rodando.

    Áudio e injeção de teclas vivem em `plataforma/` (D-42). O que fica aqui é o que não
    depende de sistema: despacho por tipo de ação, e a tradução do texto de atalho vindo
    da UI para uma combinação normalizada.
    """

    def __init__(self, obs_controller, modo="automatico"):
        self.obs = obs_controller
        self.modo = str(modo or "automatico").lower()

    def executar(self, tipo, valor=None):
        if self.modo == "teste":
            logger.info("Ação bloqueada pelo Modo Teste: tipo=%s valor=%s", tipo, valor)
            return

        if tipo == "trocar_cena":
            if self.obs and self.obs.connected:
                # Devolve a mensagem para quem chamou poder mostrar na UI. Cena
                # inexistente falhava só no log, e o usuário ficava sem saber por quê.
                ok, mensagem = self.obs.trocar_cena(valor)
                return mensagem if not ok else ""

            logger.warning("OBS não conectado para trocar cena")
            return "OBS não conectado"

        elif tipo == "iniciar_live":
            if self.obs and self.obs.connected and self.obs.cliente:
                self.obs.cliente.start_stream()

        elif tipo == "parar_live":
            if self.obs and self.obs.connected and self.obs.cliente:
                self.obs.cliente.stop_stream()

        elif tipo == "tocar_som":
            plataforma.tocar_som(valor)

        elif tipo == "atalho":
            self._acionar_atalho(valor)

        else:
            logger.warning("Ação desconhecida: %s", tipo)


    def _acionar_atalho(self, hotkey_texto):
        if not hotkey_texto:
            return

        try:
            atalho = self._normalizar_atalho(hotkey_texto)
            if not atalho:
                logger.warning("Atalho inválido ignorado: '%s'", hotkey_texto)
                return

            partes = atalho.split("+")
            mods, tecla = partes[:-1], partes[-1]

            # "ctrl+shift" sem tecla final não é atalho — é modificador solto.
            if tecla in {"ctrl", "shift", "alt", "windows"}:
                logger.warning("Atalho sem tecla final ignorado: '%s'", atalho)
                return

            if plataforma.enviar_atalho(mods, tecla):
                logger.info("Atalho enviado: %s", atalho)
            else:
                logger.warning("Não foi possível enviar o atalho: %s", atalho)
        except Exception as exc:
            logger.exception("Falha ao acionar atalho '%s': %s", hotkey_texto, exc)

    def _normalizar_atalho(self, hotkey_texto):
        """Converte o texto da UI numa combinação normalizada: "ctrl+shift+z"."""
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
