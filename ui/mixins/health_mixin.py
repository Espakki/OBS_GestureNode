"""O painel de saúde. Ver D-48.

Antes, este arquivo decidia o estado do sistema lendo texto:

    if "falha ao iniciar câmera" in text_lower:
    obs_status_text = self.obs_status_label.text().lower()

A segunda linha é a que doía: o painel lia o estado **de dentro do texto de um label**, o
que fazia do widget a fonte da verdade. Renomear uma mensagem quebrava o painel sem que
nada acusasse.

Agora a engine emite `Evento` tipado (`core/estado_runtime.py`), a transição é uma função
pura, e este arquivo só pinta o resultado. Ele deixou de interpretar e passou a exibir —
que é o que uma camada de apresentação deve fazer.
"""

from core.estado_runtime import EstadoCamera, EstadoEngine, EstadoOBS, Saude, aplicar

# Um tom por severidade. Mesma paleta do resto do tema.
CORES = {
    "ok": "#22c55e",
    "warn": "#f59e0b",
    "error": "#ef4444",
    "idle": "#94a3b8",
}

# Cada estado vira (severidade, texto). Tabela em vez de cadeia de `if`: acrescentar um
# estado passa a ser uma linha, e esquecer um vira KeyError na hora, não silêncio.
APARENCIA_CAMERA = {
    EstadoCamera.RODANDO: ("ok", "Em execução"),
    EstadoCamera.LIMITADA: ("warn", "Em execução com limite"),
    EstadoCamera.FALHOU: ("error", "Falha ao iniciar"),
    EstadoCamera.PARADA: ("idle", "Pronta"),
}

APARENCIA_OBS = {
    EstadoOBS.CONECTADO: ("ok", "Conectado"),
    EstadoOBS.CONECTANDO: ("warn", "Conectando..."),
    EstadoOBS.FALHOU: ("error", "Falha de conexão"),
    EstadoOBS.DESATIVADO: ("idle", "Desativado (modo Teste)"),
    EstadoOBS.NAO_TESTADO: ("idle", "Não testado"),
}

MODOS_QUE_USAM_OBS = ("manual", "automatico")


class HealthMixin:

    def _init_saude(self):
        self.saude = Saude()

    def ao_receber_evento_da_engine(self, evento, detalhe):
        """Ligado ao sinal `evento` da engine. Transição pura, depois repinta."""
        self.saude = aplicar(self.saude, evento, detalhe)
        self._refresh_health_panels()

    def _set_health_label(self, label_widget, titulo, severidade, detalhe):
        cor = CORES.get(severidade, CORES["idle"])
        label_widget.setText(f"● {titulo}: {detalhe}")
        label_widget.setStyleSheet(f"color: {cor}; font-weight: 600;")

    def _detalhe_da_camera(self):
        severidade, texto = APARENCIA_CAMERA[self.saude.camera]

        if self.saude.camera is EstadoCamera.PARADA:
            nome = self.camera_device_combo.currentText() or "Câmera"
            return severidade, f"Pronta ({nome})"

        # O detalhe que veio da engine é mais específico que o rótulo genérico — é ele que
        # diz *qual* limite ou *qual* falha.
        return severidade, self.saude.detalhe_camera or texto

    def _severidade_do_obs(self, modo):
        if modo not in MODOS_QUE_USAM_OBS:
            return APARENCIA_OBS[EstadoOBS.DESATIVADO]

        if (
            self.saude.obs is EstadoOBS.NAO_TESTADO
            and self.saude.engine is EstadoEngine.RODANDO
        ):
            return "warn", "Aguardando conexão"

        return APARENCIA_OBS[self.saude.obs]

    def _refresh_health_panels(self):
        modo = self.estado.modo

        severidade, detalhe = self._detalhe_da_camera()
        self._set_health_label(self.health_camera, "Câmera", severidade, detalhe)

        severidade, detalhe = self._severidade_do_obs(modo)
        self._set_health_label(self.health_obs, "OBS", severidade, detalhe)

        ativos = self.estado.gestos_ativos
        if not ativos:
            self._set_health_label(self.health_gestos, "Gestos", "warn", "Nenhum gesto ativo")
        else:
            self._set_health_label(
                self.health_gestos, "Gestos", "ok", f"{len(ativos)} gesto(s) ativos"
            )

    def marcar_obs(self, estado, detalhe=""):
        """O teste manual de conexão não passa pela engine, mas alimenta a mesma saúde."""
        self.saude = self.saude.com(obs=estado, detalhe_obs=detalhe)
        self._refresh_health_panels()

    def marcar_engine(self, estado):
        self.saude = self.saude.com(engine=estado)
        if estado is EstadoEngine.PARADA:
            self.saude = self.saude.com(camera=EstadoCamera.PARADA, detalhe_camera="")
        self._refresh_health_panels()
