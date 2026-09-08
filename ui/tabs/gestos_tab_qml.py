"""A aba Gestos em QML. Ver D-49.

Contrato:

    escolherGestosPedido()   abrir o diálogo de quais gestos ficam na grade
    procurarSomPedido()      abrir o seletor de arquivo do sistema
    bindingEditado()         algum campo do gesto mudou (a engine precisa saber)

    definir_gestos(entradas, selecionado)   entradas = [(nome, caminho_do_icone)]
    gesto_atual() -> str
    definir_arquivo_de_som(caminho)

Os campos gravam direto no `EstadoApp` pela ponte — cena, som e atalho só guardam valor.
O que sai como pedido é o que tem consequência fora do estado: abrir diálogo, abrir seletor
de arquivo, reconfigurar a engine em execução.
"""

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtQuickWidgets import QQuickWidget

from ui.qml.ponte_gestos import PonteGestos
from util.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_QML = Path(__file__).resolve().parent.parent / "qml"


class GestosTabQml(QQuickWidget):

    gestoSelecionado = Signal(str)
    escolherGestosPedido = Signal()
    procurarSomPedido = Signal()
    bindingEditado = Signal()

    def __init__(self, estado, parent=None):
        super().__init__(parent)

        self.ponte = PonteGestos(estado, parent=self)
        self.ponte.gestoTrocado.connect(self.gestoSelecionado)
        self.ponte.escolherGestosPedido.connect(self.escolherGestosPedido)
        self.ponte.procurarSomPedido.connect(self.procurarSomPedido)
        self.ponte.bindingEditado.connect(self.bindingEditado)

        self.rootContext().setContextProperty("ponteGestos", self.ponte)
        self.engine().addImportPath(str(DIRETORIO_QML))
        self.setClearColor(QColor("#0d0d0d"))
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "GestosTab.qml")))

        if self.status() == QQuickWidget.Error:
            for erro in self.errors():
                logger.error("QML: %s", erro.toString())

    def definir_gestos(self, entradas, selecionado):
        """`entradas` traz caminho de arquivo; o QML precisa de URL."""
        convertidas = [
            (nome, QUrl.fromLocalFile(str(caminho)).toString() if caminho else "")
            for nome, caminho in entradas
        ]
        self.ponte.definir_gestos(convertidas, selecionado)

    def gesto_atual(self):
        return self.ponte.gestoAtual

    def refletir_binding(self):
        """No-op: os campos leem a ponte por ligação, como na aba Geral.

        Existe para cumprir o contrato — a versão em Widgets precisa de fato empurrar os
        dez campos do formulário, e quem chama não deve saber a diferença.
        """

    def definir_arquivo_de_som(self, caminho):
        self.ponte.definirArquivoDeSom(caminho)
