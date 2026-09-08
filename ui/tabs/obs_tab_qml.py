"""A aba OBS em QML. Ver D-49.

Contrato, igual ao da aba Geral — sinais de intenção e métodos de reflexo:

    testePedido()                   o usuário mandou testar a conexão
    credenciaisMudaram()            host, porta ou senha mudaram

    definir_status(situacao, detalhe="")   `situacao` é um `EstadoOBS`
    texto_do_status() -> str

A janela não toca em campo nenhum: as credenciais moram no `EstadoApp` e a tela as lê por
ligação. Era isto que antes exigia `self.obs_host.text().strip()` espalhado pelo mixin.
"""

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtQuickWidgets import QQuickWidget

from core.estado_runtime import EstadoOBS
from ui.qml.ponte_obs import PonteObs
from util.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_QML = Path(__file__).resolve().parent.parent / "qml"


class ObsTabQml(QQuickWidget):

    testePedido = Signal()
    credenciaisMudaram = Signal()

    def __init__(self, estado, parent=None):
        super().__init__(parent)

        self.ponte = PonteObs(estado, parent=self)
        self.ponte.testePedido.connect(self.testePedido)
        self.ponte.credenciaisMudaram.connect(self.credenciaisMudaram)

        self.rootContext().setContextProperty("ponteObs", self.ponte)
        self.engine().addImportPath(str(DIRETORIO_QML))
        self.setClearColor(QColor("#0d0d0d"))
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "ObsTab.qml")))

        if self.status() == QQuickWidget.Error:
            for erro in self.errors():
                logger.error("QML: %s", erro.toString())

    def definir_status(self, situacao, detalhe=""):
        self.ponte.definir_status(situacao, detalhe)

    def texto_do_status(self):
        return self.ponte.status

    def definir_controles_habilitados(self, ligado):
        """A aba OBS não trava com a engine rodando: trocar host não reabre câmera."""
