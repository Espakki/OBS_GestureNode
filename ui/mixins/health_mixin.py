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

    def _detalhe_da_camera(self):
        severidade, texto = APARENCIA_CAMERA[self.saude.camera]

        if self.saude.camera is EstadoCamera.PARADA:
            nome, _ = self.geral_tab.camera_atual()
            return severidade, f"Pronta ({nome or 'Câmera'})"

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
        """Monta as três linhas e entrega. Quem pinta é a aba — ver `geral_contrato`."""
        severidade_camera, detalhe_camera = self._detalhe_da_camera()
        severidade_obs, detalhe_obs = self._severidade_do_obs(self.estado.modo)

        ativos = self.estado.gestos_ativos
        if ativos:
            gestos = ("ok", f"{len(ativos)} gesto(s) ativos")
        else:
            gestos = ("warn", "Nenhum gesto ativo")

        self.geral_tab.definir_saude(
            [
                ("Câmera", severidade_camera, detalhe_camera),
                ("OBS", severidade_obs, detalhe_obs),
                ("Gestos", gestos[0], gestos[1]),
            ]
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
