"""A aba Geral em QML, hospedada dentro da janela de Widgets. Ver D-49.

**Como as duas tecnologias convivem.** `QQuickWidget` é um `QWidget` que renderiza uma cena
QML. Para o `QTabWidget` ele é uma aba como qualquer outra — o que torna a migração
incremental de verdade: uma aba por vez, com o app rodando o tempo todo, em vez de um
"big bang" que só se prova no fim.

Cumpre o mesmo `ui/tabs/geral_contrato.py` que a versão em Widgets, então a janela não sabe
qual das duas está montada.

**Os `set_*` aqui são quase todos no-op, e isso é o ponto — não preguiça.** Na versão
Widgets eles empurravam valor para dentro do widget, e cada um precisava da guarda do D-41
para o `setChecked` não parecer um clique do usuário. Aqui a tela lê o estado por ligação
viva: quando o estado muda, o botão muda sozinho. Não há o que empurrar, logo não há o que
guardar. As 43 guardas resolviam um problema que, deste lado, não chega a existir.
"""

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtQuickWidgets import QQuickWidget

from ui.qml.ponte import PonteGeral
from util.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_QML = Path(__file__).resolve().parent.parent / "qml"


class GeralTabQml(QQuickWidget):
    """Hospeda `GeralTab.qml` e mantém a ponte viva."""

    modoPedido = Signal(str)
    maosPedidas = Signal(int)
    resolucaoPedida = Signal(str)
    fpsPedido = Signal(int)
    cameraPedida = Signal(int)
    esqueletoPedido = Signal(bool, bool)
    recomendadoPedido = Signal()

    def __init__(self, estado, parent=None):
        super().__init__(parent)

        self._estado = estado
        self._entradas = []
        self.ponte = PonteGeral(estado, parent=self)

        # A ponte fala em posição da lista; o contrato fala em índice do dispositivo. A
        # tradução acontece aqui, num lugar só — trocá-los abre a câmera errada.
        self.ponte.modoPedido.connect(self.modoPedido)
        self.ponte.maosPedidas.connect(self.maosPedidas)
        self.ponte.resolucaoPedida.connect(self.resolucaoPedida)
        self.ponte.fpsPedido.connect(self.fpsPedido)
        self.ponte.esqueletoPedido.connect(self.esqueletoPedido)
        self.ponte.recomendadoPedido.connect(self.recomendadoPedido)
        self.ponte.cameraPedida.connect(self._ao_pedir_camera)

        # `contextProperty` antes do `setSource`: o QML avalia as ligações ao carregar, e
        # uma `ponte` ausente nesse instante viraria erro em cada binding.
        self.rootContext().setContextProperty("ponte", self.ponte)

        # O diretório precisa estar no import path para o `qmldir` ser encontrado — é ele
        # que declara o singleton `Tema`.
        self.engine().addImportPath(str(DIRETORIO_QML))

        # O padrão do QQuickWidget é branco, e ele vaza nas bordas antes de o QML pintar.
        self.setClearColor(QColor("#0d0d0d"))

        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "GeralTab.qml")))

        if self.status() == QQuickWidget.Error:
            for erro in self.errors():
                logger.error("QML: %s", erro.toString())

    def _ao_pedir_camera(self, posicao):
        if 0 <= posicao < len(self._entradas):
            self.cameraPedida.emit(int(self._entradas[posicao][1]))

    # ------------------------------------------------------------------ contrato

    def set_mode(self, modo):
        """No-op: o QML lê `ponte.modo` por ligação. Ver o cabeçalho do módulo."""

    def set_max_maos(self, valor):
        """No-op: ligado a `ponte.maxMaos`."""

    def set_resolution(self, rotulo):
        """No-op: ligado a `ponte.resolucao`."""

    def set_fps(self, valor):
        """No-op: ligado a `ponte.fps`."""

    def set_esqueleto(self, no_preview, na_saida_obs):
        """No-op: ligado a `ponte.esqueletoPreview` e `ponte.esqueletoObs`."""

    def definir_cameras(self, entradas, indice_do_dispositivo):
        self._entradas = list(entradas)
        posicao = 0
        for i, (_, indice) in enumerate(self._entradas):
            if int(indice) == int(indice_do_dispositivo):
                posicao = i
                break
        self.ponte.definir_cameras([nome for nome, _ in self._entradas], posicao)

    def camera_atual(self):
        posicao = self.ponte.cameraSelecionada
        if 0 <= posicao < len(self._entradas):
            nome, indice = self._entradas[posicao]
            return nome, int(indice)
        return "", 0

    def definir_capacidades(self, resolucoes_off, fps_off, aviso, tem_recomendacao):
        self.ponte.definir_capacidades(resolucoes_off, fps_off, aviso, tem_recomendacao)

    def definir_saude(self, linhas):
        self.ponte.definir_saude(linhas)

    def definir_controles_habilitados(self, ligado):
        # Sem a engine parada não se troca resolução nem câmera; o QML lê isto por ligação.
        self.ponte.definir_controles_habilitados(bool(ligado))

    def update_latency_badge(self, ms):
        self.ponte.definir_latencia(ms)

    def reset_latency_badge(self):
        self.ponte.definir_latencia(None)
