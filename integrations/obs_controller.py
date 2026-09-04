import obsws_python as obs
from obsws_python.error import OBSSDKRequestError
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
        """Troca a cena do OBS. Devolve `(ok, mensagem)`.

        **Uma requisição recusada não derruba a conexão.** Antes qualquer exceção zerava
        `connected` e `cliente`, então um único nome de cena inexistente matava o OBS até
        a engine reiniciar: o usuário corrigia o nome e continuava sem funcionar, porque
        já não havia conexão. Ver D-37.

        `OBSSDKRequestError` significa que o OBS respondeu recusando — a conexão está viva.
        Qualquer outra exceção é tratada como conexão perdida.
        """
        if not self.connected or not self.cliente:
            return False, "OBS não conectado"

        try:
            self.cliente.set_current_program_scene(nome_cena)
            return True, ""
        except OBSSDKRequestError as exc:
            logger.warning("OBS recusou a troca para %r: %s", nome_cena, exc)
            return False, f'OBS não tem a cena "{nome_cena}"'
        except Exception as exc:
            logger.exception("Conexão com o OBS caiu ao trocar cena: %s", exc)
            self.connected = False
            self.cliente = None
            return False, "Conexão com o OBS caiu"