import obsws_python as obs
import time
from util.logger import get_logger


logger = get_logger(__name__)

class OBSController:

    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password

        self.cliente = None
        self.connected = False

    def connect(self):
        logger.info("Iniciando conexão OBS...")
        inicio = time.time()

        self.cliente = obs.ReqClient(
            host=self.host,
            port=self.port,
            password=self.password,
            timeout=5
        )

        # D-04: Handshake — verifica que a conexão é funcional antes de setar connected
        self.cliente.get_version()  # lança OBSSDKTimeoutError ou OBSSDKRequestError se falhar

        self.connected = True

        logger.info("Conectado ao OBS!")
        logger.info("Tempo OBS: %.3fs", time.time() - inicio)

    def disconnect(self):
        if self.cliente is not None:
            try:
                self.cliente.disconnect()
            except Exception:
                pass
            self.cliente = None
        self.connected = False

    def listar_cenas(self):
        if not self.connected or not self.cliente:
            raise RuntimeError("OBS não conectado")

        return self.cliente.get_scene_list().scenes

    def trocar_cena(self, nome_cena):
        if not self.connected or not self.cliente:
            return False

        try:
            self.cliente.set_current_program_scene(nome_cena)
            return True
        except Exception as exc:
            logger.exception("Erro ao trocar cena no OBS: %s", exc)
            self.connected = False
            self.cliente = None
            return False