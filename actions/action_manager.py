import os
import platform
import winsound

try:
    import keyboard
except Exception:
    keyboard = None

from util.logger import get_logger


logger = get_logger(__name__)


class ActionManager:
    def __init__(self, obs_controller):
        self.obs = obs_controller

    def executar(self, tipo, valor=None):
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

        if keyboard is None:
            logger.warning("Pacote 'keyboard' não disponível para acionar atalho")
            return

        try:
            atalho = hotkey_texto.replace(" ", "")
            keyboard.send(atalho)
        except Exception as exc:
            logger.exception("Falha ao acionar atalho '%s': %s", hotkey_texto, exc)