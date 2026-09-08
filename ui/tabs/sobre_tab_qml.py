"""A aba Sobre. Ver D-51.

Sem contrato próprio: ela não tem estado do app para refletir nem intenção para emitir —
só mostra versão e licenças. Inventar sinais aqui seria cerimônia sem conteúdo.

Sem fallback de Widgets também, e por isso ela é **opcional**: se o QML falhar, a aba
simplesmente não aparece, em vez de o app não abrir. É a única aba de que se pode abrir mão.
"""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuickWidgets import QQuickWidget

from ui.qml.ponte_sobre import PonteSobre
from util.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_QML = Path(__file__).resolve().parent.parent / "qml"


class SobreTabQml(QQuickWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ponte = PonteSobre(parent=self)
        self.rootContext().setContextProperty("ponteSobre", self.ponte)
        self.engine().addImportPath(str(DIRETORIO_QML))
        self.setClearColor(QColor("#0d0d0d"))
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "SobreTab.qml")))

        if self.status() == QQuickWidget.Error:
            motivos = "; ".join(erro.toString() for erro in self.errors())
            logger.error("QML da aba Sobre não carregou: %s", motivos)
            raise RuntimeError(motivos or "QML não carregou")
