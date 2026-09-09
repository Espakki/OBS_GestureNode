"""O que a casca precisa e que nenhuma das pontes de aba cobre.

As quatro pontes existentes (`ponte.py`, `ponte_gestos.py`, `ponte_obs.py`, `ponte_sobre.py`)
já expõem o conteúdo das telas. O que faltava era o que mora **fora** delas: o estado da
engine, o preview, o log e o histórico de disparos — que na interface de Widgets estão
espalhados por `status_label`, `obs_footer_label`, `log_view`, `preview_label` e os três
botões do rodapé.

Segue a mesma assimetria das outras pontes (ver o cabeçalho de `ui/qml/ponte.py`):
estado → tela por `@Property` com `notify`, tela → Python por `@Slot` que emite intenção.
Nenhuma propriedade é gravável pelo QML.
"""

import time

from PySide6.QtCore import Property, QObject, QSize, Signal, Slot

from util.logger import get_logger

logger = get_logger(__name__)

MAX_DISPAROS = 6
MAX_LOG = 200


class PonteShell(QObject):
    """A barra superior, o preview e a gaveta de diagnóstico."""

    mudou = Signal()
    frameMudou = Signal()
    logMudou = Signal()
    disparosMudaram = Signal()

    # Intenções da casca. A janela liga cada uma ao método que já existia.
    iniciarPedido = Signal()
    pararPedido = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rodando = False
        self._pode_iniciar = True
        self._pode_parar = False
        self._estado_texto = "Parado"
        self._obs_texto = "OBS não testado"
        self._obs_ok = False
        self._latencia_curta = ""
        self._contador = 0
        self._tem_frame = False
        self._tamanho_do_preview = QSize(640, 360)
        self._log = []
        self._disparos = []

    # ------------------------------------------------------------------ engine

    @Property(bool, notify=mudou)
    def rodando(self):
        return self._rodando

    @Property(bool, notify=mudou)
    def podeIniciar(self):
        return self._pode_iniciar

    @Property(bool, notify=mudou)
    def podeParar(self):
        return self._pode_parar

    @Property(str, notify=mudou)
    def estadoTexto(self):
        return self._estado_texto

    def definir_estado(self, texto=None, rodando=None, pode_iniciar=None, pode_parar=None):
        if texto is not None:
            self._estado_texto = str(texto)
        if rodando is not None:
            self._rodando = bool(rodando)
        if pode_iniciar is not None:
            self._pode_iniciar = bool(pode_iniciar)
        if pode_parar is not None:
            self._pode_parar = bool(pode_parar)
        self.mudou.emit()

    @Slot()
    def iniciar(self):
        self.iniciarPedido.emit()

    @Slot()
    def parar(self):
        self.pararPedido.emit()

    # --------------------------------------------------------------------- OBS

    @Property(str, notify=mudou)
    def obsTexto(self):
        return self._obs_texto

    @Property(bool, notify=mudou)
    def obsConectado(self):
        return self._obs_ok

    def definir_obs(self, texto):
        """Recebe o mesmo texto que ia para o rodapé, e tira dele o emoji.

        O rodapé de Widgets carrega o estado dentro de um emoji ("🟢 OBS: Conectado"), o
        que é exatamente o padrão que o D-48 tirou do painel de saúde: estado transportado
        dentro de texto. Aqui o emoji vira booleano na entrada e não sobrevive à fronteira.
        """
        bruto = str(texto or "")
        self._obs_ok = "🟢" in bruto
        limpo = bruto.replace("🟢", "").replace("🔴", "").replace("⚠️", "").replace("⏳", "")
        self._obs_texto = limpo.strip() or "OBS"
        self.mudou.emit()

    # ---------------------------------------------------------------- latência

    @Property(str, notify=mudou)
    def latenciaCurta(self):
        return self._latencia_curta

    def definir_latencia(self, ms):
        self._latencia_curta = "" if ms is None else f"{ms:.0f} ms"
        self.mudou.emit()

    # ----------------------------------------------------------------- preview

    @Property(int, notify=frameMudou)
    def contadorDeFrames(self):
        return self._contador

    @Property(bool, notify=frameMudou)
    def temFrame(self):
        return self._tem_frame

    def novo_frame(self):
        """Avisa o QML que o provedor tem imagem nova.

        O contador entra na URL (`image://preview/<n>`) porque o Qt guarda a imagem em
        cache pela URL: sem ele a `Image` acharia que já tem aquele endereço e não pediria
        de novo — o preview congelaria no primeiro quadro.
        """
        self._contador += 1
        self._tem_frame = True
        self.frameMudou.emit()

    def limpar_frame(self):
        self._tem_frame = False
        self.frameMudou.emit()

    @Slot(int, int)
    def definirTamanhoDoPreview(self, largura, altura):
        """O QML informa o tamanho real da área de preview.

        A janela reduz o quadro antes de entregar (`MainWindow.update_frame`), e sem esse
        número ela reduziria para um tamanho chutado — grande demais desperdiça CPU a cada
        quadro, pequeno demais borra a imagem ao ser ampliada de volta.
        """
        if largura > 0 and altura > 0:
            self._tamanho_do_preview = QSize(int(largura), int(altura))

    def tamanho_do_preview(self):
        return self._tamanho_do_preview

    # --------------------------------------------------------------------- log

    @Property(list, notify=logMudou)
    def log(self):
        return list(self._log)

    def adicionar_log(self, texto):
        if not texto:
            return
        carimbo = time.strftime("%H:%M:%S")
        self._log.append(f"{carimbo}  {texto}")
        del self._log[:-MAX_LOG]
        self.logMudou.emit()

    # ---------------------------------------------------------------- disparos

    @Property(list, notify=disparosMudaram)
    def disparos(self):
        return list(self._disparos)

    def registrar_disparo(self, texto):
        """Histórico curto do que os gestos fizeram. Durante a live ninguém lê log."""
        if not texto:
            return
        self._disparos.insert(0, {"quando": time.strftime("%H:%M"), "texto": str(texto)})
        del self._disparos[MAX_DISPAROS:]
        self.disparosMudaram.emit()

    @Property(str, notify=disparosMudaram)
    def ultimoGesto(self):
        return self._disparos[0]["texto"].split(" → ")[0] if self._disparos else ""

    @Property(str, notify=disparosMudaram)
    def ultimaAcao(self):
        if not self._disparos:
            return ""
        partes = self._disparos[0]["texto"].split(" → ", 1)
        return partes[1] if len(partes) > 1 else ""
