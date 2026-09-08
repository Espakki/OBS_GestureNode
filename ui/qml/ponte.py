"""O `EstadoApp` exposto ao QML como propriedades observáveis. Ver D-49.

**Por que esta camada é fina.** O `EstadoApp` foi escrito sem depender de Qt (D-47), o que
parecia purismo na hora e é o que paga agora: adaptar um estado que já notifica mudanças
para o modelo de propriedades do QML é traduzir nomes, não reimplementar lógica.

O caminho é de mão dupla e assimétrico de propósito:

- **estado → tela** é automático. `escutar()` no `EstadoApp` dispara os sinais `NOTIFY`, e
  o QML redesenha o que dependia daquele valor. Ninguém chama `set_*`.
- **tela → estado** passa por métodos `Slot` explícitos, e não por propriedades graváveis.
  Alguns cliques têm consequência além de guardar um valor — trocar o número de mãos pede
  confirmação e reinicia a captura (D-06) — então quem decide isso continua sendo o Python,
  não a view.

Essa assimetria é o que dissolve o problema do D-41: "refletir o estado" e "o usuário
clicou" deixam de ser a mesma operação, então não há o que guardar com `blockSignals`.
"""

from PySide6.QtCore import Property, QObject, Signal, Slot

from core.estado_runtime import EstadoCamera, EstadoEngine, EstadoOBS
from ui.presets import RESOLUTION_PRESETS, RESOLUTION_PRESETS_REVERSED
from util.logger import get_logger

logger = get_logger(__name__)

AJUDA_POR_MODO = {
    "teste": "Detecta gestos sem executar nada — para calibrar.",
    "manual": "Conecta ao OBS e executa as ações. Sem câmera virtual.",
    "automatico": "Conecta ao OBS e liga a câmera virtual ao iniciar.",
}

CORES_DE_SEVERIDADE = {
    "ok": "#22c55e",
    "warn": "#f59e0b",
    "error": "#ef4444",
    "idle": "#94a3b8",
}


class PonteGeral(QObject):
    """Ponte da aba Geral. Uma por janela."""

    mudou = Signal()  # um sinal só: a aba é pequena e redesenhar tudo é barato
    camerasMudaram = Signal()
    saudeMudou = Signal()
    latenciaMudou = Signal()

    # Pedidos que a view faz ao Python. A janela conecta cada um ao handler que já existia.
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

        self._cameras = []
        self._camera_selecionada = 0
        self._resolucoes_indisponiveis = []
        self._fps_indisponiveis = []
        self._aviso = ""
        self._tem_recomendacao = False
        self._latencia = "Latência: aguardando..."
        self._cor_latencia = "#a0a0a0"
        self._saude = []
        self._controles_habilitados = True

        # É isto que faz a tela seguir o estado sem ninguém empurrar.
        self._cancelar = estado.escutar(self._ao_mudar_estado)

    def _ao_mudar_estado(self, campo, valor):
        self.mudou.emit()

    # ------------------------------------------------------------------ estado direto

    @Property(str, notify=mudou)
    def modo(self):
        return self._estado.modo

    @Property(str, notify=mudou)
    def ajudaDoModo(self):
        return AJUDA_POR_MODO.get(self._estado.modo, "")

    @Property(int, notify=mudou)
    def maxMaos(self):
        return int(self._estado.max_maos)

    @Property(bool, notify=mudou)
    def esqueletoPreview(self):
        return bool(self._estado.mostrar_esqueleto)

    @Property(bool, notify=mudou)
    def esqueletoObs(self):
        return bool(self._estado.esqueleto_na_vcam)

    @Property(str, notify=mudou)
    def resolucao(self):
        par = (self._estado.camera_largura, self._estado.camera_altura)
        return RESOLUTION_PRESETS_REVERSED.get(par, "720p")

    @Property(int, notify=mudou)
    def fps(self):
        return int(self._estado.camera_fps)

    # --------------------------------------------------------- o que a janela alimenta

    @Property(list, notify=camerasMudaram)
    def cameras(self):
        return list(self._cameras)

    @Property(int, notify=camerasMudaram)
    def cameraSelecionada(self):
        return self._camera_selecionada

    def definir_cameras(self, nomes, selecionada):
        self._cameras = list(nomes)
        self._camera_selecionada = int(selecionada)
        self.camerasMudaram.emit()

    @Property(list, notify=mudou)
    def resolucoesIndisponiveis(self):
        return list(self._resolucoes_indisponiveis)

    @Property(list, notify=mudou)
    def fpsIndisponiveis(self):
        return list(self._fps_indisponiveis)

    @Property(str, notify=mudou)
    def avisoDaCamera(self):
        return self._aviso

    @Property(bool, notify=mudou)
    def temRecomendacao(self):
        return self._tem_recomendacao

    def definir_capacidades(self, resolucoes_off, fps_off, aviso, tem_recomendacao):
        self._resolucoes_indisponiveis = list(resolucoes_off)
        self._fps_indisponiveis = [int(f) for f in fps_off]
        self._aviso = aviso or ""
        self._tem_recomendacao = bool(tem_recomendacao)
        self.mudou.emit()

    @Property(str, notify=latenciaMudou)
    def latencia(self):
        return self._latencia

    @Property(str, notify=latenciaMudou)
    def corDaLatencia(self):
        return self._cor_latencia

    def definir_latencia(self, ms):
        """`None` volta ao estado de espera. As faixas são as mesmas da versão Widgets."""
        if ms is None:
            self._latencia = "Latência: aguardando..."
            self._cor_latencia = "#a0a0a0"
        else:
            if ms <= 33:
                cor, rotulo = "#22c55e", "Ótima"
            elif ms <= 66:
                cor, rotulo = "#f59e0b", "Boa"
            else:
                cor, rotulo = "#ef4444", "Lenta"
            self._latencia = f"⚡ Latência de processamento: {ms:.0f}ms — {rotulo}"
            self._cor_latencia = cor
        self.latenciaMudou.emit()

    @Property(bool, notify=mudou)
    def controlesHabilitados(self):
        return self._controles_habilitados

    def definir_controles_habilitados(self, ligado):
        self._controles_habilitados = bool(ligado)
        self.mudou.emit()

    @Property(list, notify=saudeMudou)
    def saude(self):
        return list(self._saude)

    def definir_saude(self, linhas):
        """`linhas` é uma sequência de `(titulo, severidade, detalhe)`."""
        self._saude = [
            {
                "texto": f"{titulo}: {detalhe}",
                "cor": CORES_DE_SEVERIDADE.get(severidade, CORES_DE_SEVERIDADE["idle"]),
            }
            for titulo, severidade, detalhe in linhas
        ]
        self.saudeMudou.emit()

    # ------------------------------------------------------------------ ações da view

    @Slot(str)
    def escolherModo(self, modo):
        self.modoPedido.emit(modo)

    @Slot(int)
    def escolherMaos(self, quantidade):
        self.maosPedidas.emit(int(quantidade))

    @Slot(str)
    def escolherResolucao(self, rotulo):
        if rotulo in RESOLUTION_PRESETS:
            self.resolucaoPedida.emit(rotulo)

    @Slot(int)
    def escolherFps(self, valor):
        self.fpsPedido.emit(int(valor))

    @Slot(int)
    def escolherCamera(self, indice):
        self.cameraPedida.emit(int(indice))

    @Slot(bool)
    def alternarEsqueletoPreview(self, ligado):
        self._estado.mostrar_esqueleto = bool(ligado)
        self.esqueletoPedido.emit(
            self._estado.mostrar_esqueleto, self._estado.esqueleto_na_vcam
        )

    @Slot(bool)
    def alternarEsqueletoObs(self, ligado):
        self._estado.esqueleto_na_vcam = bool(ligado)
        self.esqueletoPedido.emit(
            self._estado.mostrar_esqueleto, self._estado.esqueleto_na_vcam
        )

    @Slot()
    def aplicarRecomendado(self):
        self.recomendadoPedido.emit()
