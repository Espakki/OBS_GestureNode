from PySide6.QtCore import QThread, Signal

from obsws_python.error import OBSSDKError, OBSSDKTimeoutError
from websocket import WebSocketTimeoutException

from integrations.obs_controller import OBSController
from util.logger import get_logger


logger = get_logger(__name__)


_MSGS_OBS = {
    "recusada": "🔴 OBS: Offline",
    "Timeout": "⚠️ OBS: Timeout",
    "Endereço": "⚠️ OBS: Host inválido",
    "Senha": "⚠️ OBS: Senha incorreta",
}


def _classificar_erro(exc: Exception) -> str:
    """Classifica a exceção e retorna mensagem acionável para o usuário."""
    if isinstance(exc, ConnectionRefusedError):
        return "Conexão recusada — abra o OBS Studio e ative o WebSocket Server"
    if isinstance(exc, (TimeoutError, WebSocketTimeoutException, OBSSDKTimeoutError)):
        return "Timeout — OBS não respondeu em 5s. Verifique o IP/porta"
    if isinstance(exc, OSError):
        # socket.gaierror é subclasse de OSError e indica DNS failure
        return "Endereço não encontrado — verifique o campo Host"
    if isinstance(exc, OBSSDKError):
        # Cobre senha errada, sem senha quando necessário, etc.
        return "Senha incorreta — verifique as configurações do WebSocket no OBS"
    return "Falha na conexão — verifique as configurações do WebSocket"


def _resumir_footer_obs(mensagem: str) -> str:
    """Mapeia mensagem detalhada de erro OBS para o texto resumido do rodapé.

    Co-localizado com _classificar_erro para que mudanças nas mensagens
    quebrem visivelmente ambas as funções ao mesmo tempo.
    """
    for chave, texto_curto in _MSGS_OBS.items():
        if chave in mensagem:
            return texto_curto
    return "⚠️ OBS: Erro"


class OBSConnectThread(QThread):
    """
    Thread não-bloqueante para tentativa de conexão com o OBS WebSocket.

    Criado por tentativa, destruído ao completar (D-02).
    Emite connected(OBSController) em sucesso, failed(str) em falha.
    """

    connected = Signal(object)   # OBSController
    failed = Signal(str)         # mensagem acionável
    connecting = Signal()

    def __init__(self, host: str, port: int, password: str, parent=None):
        super().__init__(parent)
        self._host = host
        self._port = port
        self._password = password

    def run(self):
        self.connecting.emit()
        controlador = OBSController(
            host=self._host,
            port=self._port,
            password=self._password,
        )
        try:
            controlador.connect()
            logger.info("OBSConnectThread: conexão bem-sucedida")
            self.connected.emit(controlador)
        except Exception as exc:
            logger.exception("OBSConnectThread: falha na conexão: %s", exc)
            self.failed.emit(_classificar_erro(exc))
