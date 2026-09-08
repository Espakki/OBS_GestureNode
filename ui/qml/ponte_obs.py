"""A aba OBS exposta ao QML. Ver D-49.

Host, porta e senha são gravados direto no `EstadoApp` — eles só guardam valor. É por isso
que aqui os `definir_*` escrevem em vez de emitir pedido, ao contrário da aba Geral: lá o
clique reinicia câmera e pede confirmação, e decidir isso é do Python.

O status da conexão **não** vem do estado: é do runtime, e quem sabe dele é a janela, que
dirige a thread de conexão.
"""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from core.estado_runtime import EstadoOBS

CORES = {
    EstadoOBS.CONECTADO: "#22c55e",
    EstadoOBS.CONECTANDO: "#f59e0b",
    EstadoOBS.FALHOU: "#ef4444",
    EstadoOBS.DESATIVADO: "#94a3b8",
    EstadoOBS.NAO_TESTADO: "#94a3b8",
}

TEXTO_PADRAO = {
    EstadoOBS.CONECTADO: "Conectado",
    EstadoOBS.CONECTANDO: "Conectando...",
    EstadoOBS.FALHOU: "Falha de conexão",
    EstadoOBS.DESATIVADO: "Desativado (modo Teste)",
    EstadoOBS.NAO_TESTADO: "Desconectado",
}


class PonteObs(QObject):

    mudou = Signal()
    statusMudou = Signal()

    testePedido = Signal()
    credenciaisMudaram = Signal()

    def __init__(self, estado, parent=None):
        super().__init__(parent)
        self._estado = estado
        self._situacao = EstadoOBS.NAO_TESTADO
        self._detalhe = ""

        self._cancelar = estado.escutar(lambda campo, valor: self.mudou.emit())

    def desligar(self):
        """Cancela a inscrição no estado.

        Sem isto, uma ponte destruída continua na lista de ouvintes do `EstadoApp` e
        estoura `Internal C++ object already deleted` a **cada** mudança de estado, para
        sempre. O `EstadoApp` engole a exceção (por desenho: um ouvinte quebrado não pode
        derrubar quem mexeu num slider), então o vazamento não aparece como falha — aparece
        como um traceback no log a cada clique.
        """
        if self._cancelar is not None:
            self._cancelar()
            self._cancelar = None

    # ------------------------------------------------------------------ credenciais

    @Property(str, notify=mudou)
    def host(self):
        return self._estado.obs_host

    @Property(int, notify=mudou)
    def porta(self):
        return int(self._estado.obs_porta)

    @Property(str, notify=mudou)
    def senha(self):
        return self._estado.obs_senha

    @Slot(str)
    def definirHost(self, valor):
        self._estado.obs_host = valor.strip()
        self.credenciaisMudaram.emit()

    @Slot(int)
    def definirPorta(self, valor):
        self._estado.obs_porta = int(valor)
        self.credenciaisMudaram.emit()

    @Slot(str)
    def definirSenha(self, valor):
        self._estado.obs_senha = valor
        self.credenciaisMudaram.emit()

    # ------------------------------------------------------------------ status

    @Property(str, notify=statusMudou)
    def status(self):
        return self._detalhe or TEXTO_PADRAO.get(self._situacao, "Desconectado")

    @Property(str, notify=statusMudou)
    def corDoStatus(self):
        return CORES.get(self._situacao, CORES[EstadoOBS.NAO_TESTADO])

    @Property(bool, notify=statusMudou)
    def testando(self):
        return self._situacao is EstadoOBS.CONECTANDO

    def definir_status(self, situacao, detalhe=""):
        self._situacao = situacao
        self._detalhe = detalhe or ""
        self.statusMudou.emit()

    # ------------------------------------------------------------------ ações

    @Slot()
    def testar(self):
        self.testePedido.emit()

    @Slot(str)
    def abrirLink(self, url):
        """Abre no navegador do sistema.

        Vale dizer por que não é o QML abrindo sozinho: o link é o único ponto da tela que
        leva o usuário para fora do app, e concentrá-lo aqui deixa explícito que é uma ação
        externa — não um destino dentro da interface.
        """
        QDesktopServices.openUrl(QUrl(url))
