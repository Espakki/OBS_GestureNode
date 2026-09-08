"""A aba Geral em QML, hospedada dentro da janela de Widgets. Ver D-49.

**Como as duas tecnologias convivem.** `QQuickWidget` é um `QWidget` que renderiza uma cena
QML. Para o `QTabWidget` ele é uma aba como qualquer outra — o que torna a migração
incremental de verdade: uma aba por vez, com o app rodando o tempo todo, em vez de um
"big bang" que só se prova no fim.

Este arquivo expõe a **mesma API pública** que o `GeralTab` de Widgets (`set_mode`,
`set_max_maos`, `set_resolution`, `set_fps`, `set_esqueleto`, `update_latency_badge`,
`reset_latency_badge`). Assim os mixins existentes seguem funcionando sem saber o que mudou.

Só que agora os `set_*` são quase todos **no-op**, e isso não é preguiça — é a diferença
que se quer mostrar. Na versão Widgets eles empurravam valor para dentro do widget, e cada
um precisava da guarda do D-41 para o `setChecked` não parecer um clique. Aqui a tela lê o
estado por ligação viva: quando o estado muda, o botão muda sozinho. Não há o que empurrar,
logo não há o que guardar.
"""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuickWidgets import QQuickWidget

from ui.qml.ponte import PonteGeral
from util.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_QML = Path(__file__).resolve().parent.parent / "qml"


class GeralTabQml(QQuickWidget):
    """Hospeda `GeralTab.qml` e mantém a ponte viva."""

    def __init__(self, estado, parent=None):
        super().__init__(parent)

        self.ponte = PonteGeral(estado, parent=self)

        # `contextProperty` antes do `setSource`: o QML avalia as ligações ao carregar, e
        # uma `ponte` ausente nesse instante viraria erro em cada binding.
        self.rootContext().setContextProperty("ponte", self.ponte)

        # O diretório precisa estar no import path para o `qmldir` ser encontrado — é ele
        # que declara o singleton `Tema`.
        self.engine().addImportPath(str(DIRETORIO_QML))

        # O padrão é branco, e ele vaza nas bordas antes de o QML pintar. Ver D-49.
        self.setClearColor(QColor("#0d0d0d"))

        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "GeralTab.qml")))

        if self.status() == QQuickWidget.Error:
            for erro in self.errors():
                logger.error("QML: %s", erro.toString())

    # ------------------------------------------------------------------ API compatível

    def set_mode(self, modo):
        """No-op: o QML lê `ponte.modo` por ligação. Ver o cabeçalho do módulo."""

    def set_max_maos(self, valor):
        """No-op: ligado a `ponte.maxMaos`."""

    def set_resolution(self, rotulo):
        """No-op: ligado a `ponte.resolucao`."""

    def set_fps(self, valor):
        """No-op: ligado a `ponte.fps`."""

    def set_esqueleto(self, preview, obs):
        """No-op: ligado a `ponte.esqueletoPreview` e `ponte.esqueletoObs`."""

    def update_latency_badge(self, ms):
        self.ponte.definir_latencia(f"Latência: {ms:.0f} ms")

    def reset_latency_badge(self):
        self.ponte.definir_latencia("Latência: aguardando...")
