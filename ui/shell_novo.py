"""A interface nova como uma casca só, no lugar do `QTabWidget`. Ver D-49 e D-52.

**Por que uma casca e não uma quarta aba.** A remodelagem não muda o conteúdo das telas —
muda a moldura: rail no lugar das abas, um botão no lugar de três, o estado num lugar só, o
log numa gaveta. Nada disso cabe dentro de uma aba, porque tudo isso *é* a coisa em volta
das abas.

**Ela reaproveita as quatro pontes existentes.** `PonteGeral`, `PonteGestos`, `PonteObs` e
`PonteSobre` já expõem o estado real e as intenções; a interface nova só desenha diferente.
O que faltava — engine, preview, log, disparos — mora na `PonteShell`, e é o que na versão
de Widgets estava espalhado por `status_label`, `obs_footer_label`, `log_view`,
`preview_label` e os três botões do rodapé.

**Os adaptadores no fim do arquivo existem para os mixins não mudarem.** `camera_mixin`,
`engine_mixin`, `obs_mixin` e `health_mixin` falam com `self.geral_tab`, `self.log_view`,
`self.start_button` e companhia. Em vez de reescrever os quatro, esta casca oferece objetos
com a mesma superfície e traduz para as pontes. É o mesmo princípio do
`ui/tabs/geral_contrato.py`: quem chama diz *o que* quer, não *como* desenhar.
"""

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtQuickWidgets import QQuickWidget

from ui.qml.ponte import PonteGeral
from ui.qml.ponte_gestos import PonteGestos
from ui.qml.ponte_obs import PonteObs
from ui.qml.ponte_onboarding import PonteOnboarding
from ui.qml.ponte_shell import PonteShell
from ui.qml.ponte_sobre import PonteSobre
from ui.qml.provedor_preview import ProvedorDePreview
from util.logger import get_logger

logger = get_logger(__name__)

RAIZ_QML = Path(__file__).resolve().parent / "qml"
DIRETORIO_QML = RAIZ_QML / "novo"


class ShellNovo(QQuickWidget):
    """Hospeda `novo/App.qml` e mantém as cinco pontes vivas."""

    # --- contrato da aba Geral (ui/tabs/geral_contrato.py) ---
    modoPedido = Signal(str)
    maosPedidas = Signal(int)
    resolucaoPedida = Signal(str)
    fpsPedido = Signal(int)
    cameraPedida = Signal(int)
    esqueletoPedido = Signal(bool, bool)
    recomendadoPedido = Signal()

    # --- contrato da aba Gestos ---
    gestoSelecionado = Signal(str)
    escolherGestosPedido = Signal()
    procurarSomPedido = Signal()
    bindingEditado = Signal()
    ativoAlternado = Signal(str, bool)

    # --- contrato da aba OBS ---
    testePedido = Signal()
    credenciaisMudaram = Signal()

    # --- casca ---
    iniciarPedido = Signal()
    pararPedido = Signal()

    def __init__(self, estado, todos_os_gestos, parent=None):
        super().__init__(parent)

        self._estado = estado
        self._entradas_de_camera = []

        self.ponte = PonteGeral(estado, parent=self)
        self.ponte_gestos = PonteGestos(estado, parent=self)
        self.ponte_obs = PonteObs(estado, parent=self)
        self.ponte_sobre = PonteSobre(parent=self)
        self.shell = PonteShell(parent=self)
        self.onboarding = PonteOnboarding(estado, parent=self)

        self._ligar_intencoes()

        # `contextProperty` antes do `setSource`: o QML avalia as ligações ao carregar, e
        # uma ponte ausente nesse instante viraria erro em cada binding.
        contexto = self.rootContext()
        contexto.setContextProperty("ponte", self.ponte)
        contexto.setContextProperty("ponteGestos", self.ponte_gestos)
        contexto.setContextProperty("ponteObs", self.ponte_obs)
        contexto.setContextProperty("ponteSobre", self.ponte_sobre)
        contexto.setContextProperty("shell", self.shell)
        contexto.setContextProperty("onboarding", self.onboarding)

        # O provedor é de propriedade da engine QML depois de registrado — guardar a
        # referência aqui também é o que evita o objeto ser coletado antes da hora.
        self._provedor = ProvedorDePreview()
        self.engine().addImageProvider("preview", self._provedor)

        # O import path é `ui/qml`, não `ui/qml/novo`: os arquivos declaram `import novo`
        # e o `qmldir` declara `module novo`.
        #
        # Sem esse namespace os dois conjuntos disputam nome. `ui/qml/` e `ui/qml/novo/`
        # têm ambos um `Deslizante`, e num processo com as duas interfaces vivas o tipo do
        # `novo` venceu — a aba Gestos ANTIGA passou a falhar a carregar por causa de um
        # arquivo que não é dela. O sintoma aponta para o arquivo errado, então isso custa
        # caro de diagnosticar. Ver D-52.
        self.engine().addImportPath(str(RAIZ_QML))
        self.setClearColor(QColor("#0b0b0f"))
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(DIRETORIO_QML / "App.qml")))

        self.destroyed.connect(lambda *_: self._desligar())

        self._exigir_carregamento()

        # Os doze gestos, com ícone — a grade nova mostra os inativos também.
        self.ponte_gestos.definir_todos([
            (nome, QUrl.fromLocalFile(str(caminho)).toString() if caminho else "")
            for nome, caminho in todos_os_gestos
        ])

        # Os adaptadores que os mixins enxergam.
        self.geral_tab = _AdaptadorGeral(self)
        self.gestos_tab = _AdaptadorGestos(self)
        self.obs_tab = _AdaptadorObs(self)
        self.preview_label = _AdaptadorPreview(self)
        self.status_label = _AdaptadorStatus(self.shell)
        self.obs_footer_label = _AdaptadorFooterObs(self.shell)
        self.log_view = _AdaptadorLog(self.shell)
        # O `setEnabled` que o `engine_mixin` empurra vira `podeIniciar`/`podeParar` na
        # ponte — é assim que um botão só consegue refletir o estado de dois.
        self.start_button = _BotaoFalso(
            lambda v: self.shell.definir_estado(pode_iniciar=v)
        )
        self.stop_button = _BotaoFalso(
            lambda v: self.shell.definir_estado(pode_parar=v)
        )
        self.restart_button = _BotaoFalso()

        self.shell.iniciarPedido.connect(self.start_button.clicked)
        self.shell.pararPedido.connect(self.stop_button.clicked)

    # ------------------------------------------------------------------ ligação

    def _ligar_intencoes(self):
        self.ponte.modoPedido.connect(self.modoPedido)
        self.ponte.maosPedidas.connect(self.maosPedidas)
        self.ponte.resolucaoPedida.connect(self.resolucaoPedida)
        self.ponte.fpsPedido.connect(self.fpsPedido)
        self.ponte.esqueletoPedido.connect(self.esqueletoPedido)
        self.ponte.recomendadoPedido.connect(self.recomendadoPedido)
        self.ponte.cameraPedida.connect(self._ao_pedir_camera)

        self.ponte_gestos.gestoTrocado.connect(self.gestoSelecionado)
        self.ponte_gestos.escolherGestosPedido.connect(self.escolherGestosPedido)
        self.ponte_gestos.procurarSomPedido.connect(self.procurarSomPedido)
        self.ponte_gestos.bindingEditado.connect(self.bindingEditado)
        self.ponte_gestos.ativoAlternado.connect(self.ativoAlternado)

        self.ponte_obs.testePedido.connect(self.testePedido)
        self.ponte_obs.credenciaisMudaram.connect(self.credenciaisMudaram)

    def _ao_pedir_camera(self, posicao):
        """A ponte fala em posição da lista; o contrato, em índice do dispositivo."""
        if 0 <= posicao < len(self._entradas_de_camera):
            self.cameraPedida.emit(int(self._entradas_de_camera[posicao][1]))

    def _desligar(self):
        for ponte in (self.ponte, self.ponte_gestos, self.ponte_obs):
            try:
                ponte.desligar()
            except Exception:
                logger.exception("Falha ao desligar uma ponte da casca nova")

    def _exigir_carregamento(self):
        """Levanta quando o QML não carregou. O `QQuickWidget` não levanta sozinho.

        Mesma regra das abas (ver `ui/tabs/geral_tab_qml.py`): sem isto, a falha mais
        provável — os `.qml` fora do bundle — daria uma janela em branco em vez de cair
        para a interface de abas, e a queda não seria anunciada a ninguém.
        """
        if self.status() != QQuickWidget.Error:
            return

        motivos = "; ".join(erro.toString() for erro in self.errors())
        logger.error("QML da casca nova não carregou: %s", motivos)
        self._desligar()
        raise RuntimeError(motivos or "QML não carregou")

    # ---------------------------------------------------------------- histórico

    def abrir_onboarding(self):
        """As boas-vindas como sobreposição desta janela, não como outro diálogo."""
        self.onboarding.abrir()

    def registrar_evento(self, texto):
        """Uma linha do log que também merece virar disparo, quando for gesto."""
        self.shell.adicionar_log(texto)


# ---------------------------------------------------------------------------------
# Adaptadores: a superfície que os mixins já usam, traduzida para as pontes.
# ---------------------------------------------------------------------------------


class _AdaptadorGeral(QObject):
    """Cumpre `ui/tabs/geral_contrato.py` falando com a `PonteGeral` da casca."""

    def __init__(self, casca):
        super().__init__(casca)
        self._casca = casca
        self._ponte = casca.ponte

    # os `set_*` são no-op: o QML lê o estado por ligação viva
    def set_mode(self, modo):
        pass

    def set_max_maos(self, valor):
        pass

    def set_resolution(self, rotulo):
        pass

    def set_fps(self, valor):
        pass

    def set_esqueleto(self, no_preview, na_saida_obs):
        pass

    def definir_cameras(self, entradas, indice_do_dispositivo):
        self._casca._entradas_de_camera = list(entradas)
        posicao = 0
        for i, (_, indice) in enumerate(self._casca._entradas_de_camera):
            if int(indice) == int(indice_do_dispositivo):
                posicao = i
                break
        self._ponte.definir_cameras(
            [nome for nome, _ in self._casca._entradas_de_camera], posicao
        )

    def camera_atual(self):
        posicao = self._ponte.cameraSelecionada
        entradas = self._casca._entradas_de_camera
        if 0 <= posicao < len(entradas):
            nome, indice = entradas[posicao]
            return nome, int(indice)
        return "", 0

    def definir_capacidades(self, resolucoes_off, fps_off, aviso, tem_recomendacao):
        self._ponte.definir_capacidades(resolucoes_off, fps_off, aviso, tem_recomendacao)

    def definir_saude(self, linhas):
        self._ponte.definir_saude(linhas)

    def definir_controles_habilitados(self, ligado):
        self._ponte.definir_controles_habilitados(bool(ligado))

    def update_latency_badge(self, ms):
        self._ponte.definir_latencia(ms)
        self._casca.shell.definir_latencia(ms)

    def reset_latency_badge(self):
        self._ponte.definir_latencia(None)
        self._casca.shell.definir_latencia(None)


class _AdaptadorGestos(QObject):

    def __init__(self, casca):
        super().__init__(casca)
        self._casca = casca
        self._ponte = casca.ponte_gestos

    def definir_gestos(self, entradas, selecionado):
        convertidas = [
            (nome, QUrl.fromLocalFile(str(caminho)).toString() if caminho else "")
            for nome, caminho in entradas
        ]
        self._ponte.definir_gestos(convertidas, selecionado)
        # A grade nova mostra ativo/inativo, então precisa redesenhar junto.
        self._ponte.todosMudaram.emit()

    def gesto_atual(self):
        return self._ponte.gestoAtual

    def refletir_binding(self):
        """No-op: os campos leem a ponte por ligação."""

    def definir_arquivo_de_som(self, caminho):
        self._ponte.definirArquivoDeSom(caminho)


class _AdaptadorObs(QObject):

    def __init__(self, casca):
        super().__init__(casca)
        self._ponte = casca.ponte_obs

    def definir_status(self, situacao, detalhe=""):
        self._ponte.definir_status(situacao, detalhe)

    def texto_do_status(self):
        return self._ponte.status

    def definir_controles_habilitados(self, ligado):
        """A aba OBS não trava com a engine rodando."""


class _AdaptadorPreview(QObject):
    """No lugar do `QLabel` do preview. Ver `ui/qml/provedor_preview.py`."""

    def __init__(self, casca):
        super().__init__(casca)
        self._casca = casca

    def setPixmap(self, pixmap):
        self._casca._provedor.definir(pixmap.toImage())
        self._casca.shell.novo_frame()

    def clear(self):
        self._casca._provedor.definir(None)
        self._casca.shell.limpar_frame()

    def setText(self, texto):
        """O QML já mostra "Câmera parada" quando não há frame."""

    def size(self):
        """Precisa ser um `QSize` de verdade.

        `MainWindow.update_frame` faz `QPixmap.scaled(self.preview_label.size(), ...)`, e o
        binding do PySide6 casa a assinatura por tipo, não por interface: um objeto com
        `width()` e `height()` é recusado com `TypeError`. Como isso acontece a cada quadro,
        o erro sai em loop no console assim que a câmera liga — e o preview fica preto.
        """
        return self._casca.shell.tamanho_do_preview()


class _AdaptadorStatus(QObject):
    """Só o estado da engine chega ao chip; o resto fica no log.

    O `status_label` de Widgets acumula duas coisas: o estado da engine ("Status: Parado")
    e confirmações passageiras ("Config salva!", "É preciso manter ao menos um gesto
    ativo"). No rodapé isso passa; num chip que diz se o app está detectando, não — a
    mensagem de um segundo apagaria o estado permanente.

    A tabela existe para o filtro ser explícito: texto que não estiver aqui não é estado,
    é recado, e recado vai para a gaveta de diagnóstico — que já o recebe por
    `MainWindow.update_status`, que loga tudo.
    """

    ESTADOS = {
        "Parado": False,
        "Rodando": True,
        "Parando...": False,
    }

    def __init__(self, shell):
        super().__init__(shell)
        self._shell = shell

    def setText(self, texto):
        limpo = str(texto or "")
        if limpo.startswith("Status: "):
            limpo = limpo[len("Status: "):]

        if limpo not in self.ESTADOS:
            return

        self._shell.definir_estado(texto=limpo, rodando=self.ESTADOS[limpo])


class _AdaptadorFooterObs(QObject):

    def __init__(self, shell):
        super().__init__(shell)
        self._shell = shell

    def setText(self, texto):
        self._shell.definir_obs(texto)


class _AdaptadorLog(QObject):
    """No lugar do `QPlainTextEdit`, alimentando a gaveta de diagnóstico."""

    def __init__(self, shell):
        super().__init__(shell)
        self._shell = shell

    def appendPlainText(self, texto):
        self._shell.adicionar_log(texto)
        # Toda linha é oferecida ao histórico; a ponte é que sabe reconhecer um disparo.
        # O adaptador não deve conhecer o formato das frases da engine.
        self._shell.registrar_disparo(texto)

    def setReadOnly(self, valor):
        pass

    def setMinimumHeight(self, valor):
        pass

    def document(self):
        return self

    def setMaximumBlockCount(self, valor):
        pass


class _BotaoFalso(QObject):
    """`clicked` e `setEnabled` — o que `engine_mixin` usa dos botões do rodapé.

    A casca nova tem um botão que alterna, não três. O estado de habilitado que o mixin
    empurra para `start`/`stop` vira `podeIniciar`/`podeParar` na ponte, e o QML decide o
    que mostrar. `restart_button` existe só para o `connect` do mixin não quebrar.
    """

    clicked = Signal()

    def __init__(self, ao_habilitar=None, parent=None):
        super().__init__(parent)
        self._habilitado = True
        self._ao_habilitar = ao_habilitar

    def setEnabled(self, valor):
        self._habilitado = bool(valor)
        if self._ao_habilitar is not None:
            self._ao_habilitar(self._habilitado)

    def isEnabled(self):
        return self._habilitado
