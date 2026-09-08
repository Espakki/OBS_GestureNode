from PySide6.QtWidgets import QMessageBox

from core import validacao_execucao
from core.estado_runtime import EstadoEngine
from engine.gesture_engine import GestureEngine
from ui import vinculo
from util.logger import get_logger

logger = get_logger(__name__)


class EngineMixin:

    def on_max_maos_changed(self, max_maos):
        max_maos = int(max_maos)
        anterior = int(self.config.get("max_maos", 1))

        if max_maos == anterior:
            return

        # Com a engine rodando isto derruba e religa a câmera. Antes acontecia sem aviso:
        # a imagem sumia e voltava sozinha, o que assusta no meio de uma live. Ver D-33.
        if self.engine and self.engine.isRunning():
            resposta = QMessageBox.question(
                self,
                "Reiniciar a captura?",
                f"Mudar para {max_maos} mão{'s' if max_maos > 1 else ''} exige reiniciar "
                "a captura.\n\nA câmera vai desligar e religar por alguns segundos. "
                "Continuar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resposta != QMessageBox.Yes:
                self._reverter_selecao_de_maos(anterior)
                return

        self.estado.max_maos = max_maos

        if self.engine and self.engine.isRunning():
            self.restart_engine()

    def _reverter_selecao_de_maos(self, valor):
        """Devolve os botões ao estado anterior sem disparar o handler de novo."""
        with vinculo.sem_sinais(self.maos_1_button, self.maos_2_button):
            self.geral_tab.set_max_maos(valor)

    def start_engine(self):
        erros, avisos = validacao_execucao.validar(
            self.estado.config_bruta(), self.estado.gestos_ativos
        )

        if erros:
            mensagem = "\n".join(f"• {erro}" for erro in erros)
            QMessageBox.critical(
                self,
                "Configuração inválida",
                f"Corrija os itens abaixo antes de iniciar:\n\n{mensagem}",
            )
            self.update_status("Configuração inválida para iniciar")
            return

        if avisos:
            mensagem = "\n".join(f"• {aviso}" for aviso in avisos)
            resposta = QMessageBox.question(
                self,
                "Avisos de configuração",
                f"Existem avisos de configuração:\n\n{mensagem}\n\nDeseja iniciar mesmo assim?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resposta != QMessageBox.Yes:
                self.update_status("Inicialização cancelada")
                return

        self.salvar_config_automatico()

        if self.engine and self.engine.isRunning():
            self.update_status("Engine já está em execução")
            return

        self.engine = GestureEngine(self.config)
        self.engine.frame_ready.connect(self.update_frame)
        self.engine.status_changed.connect(self.update_status)
        self.engine.latency_updated.connect(self.geral_tab.update_latency_badge)
        self.engine.fps_ajustado.connect(self.on_fps_ajustado_pela_camera)
        # Ligado AQUI, não no stop_engine. A engine também termina sozinha — falha ao
        # abrir a câmera, por exemplo — e nesses casos o sinal disparava sem ninguém
        # ouvindo: a UI ficava presa em "rodando", com Start desabilitado e um Stop que
        # não reabilitava nada, porque o `finished` já tinha passado. Ver D-34.
        self.engine.finished.connect(self.on_engine_finished)
        self.engine.evento.connect(self.ao_receber_evento_da_engine)
        self.engine.start()

        self.marcar_engine(EstadoEngine.RODANDO)
        self.status_label.setText("Status: Rodando")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.set_config_enabled(False)
        self._refresh_health_panels()

    def stop_engine(self):
        if not self.engine:
            self.update_status("Engine já está parada")
            return

        # Nenhum botão habilitado enquanto a limpeza roda — clicar Start antes da câmera
        # ser liberada dava [Errno 5] I/O error. Quem reabilita é `on_engine_finished`,
        # ligado ao sinal `finished` lá no `start_engine`.
        self.marcar_engine(EstadoEngine.PARANDO)
        self.status_label.setText("Status: Parando...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        # Limpa o preview já: os frames param no instante em que `running` vira False, mas
        # o `on_engine_finished` (que também limpa) só chega depois do `container.close()`
        # do DirectShow, ~2.2s. Sem isto a última imagem ficava congelada na tela nesse
        # intervalo, parecendo travamento.
        self._clear_preview()

        # Não bloqueia: a limpeza roda na thread da engine e a UI segue respondendo.
        self.engine.stop()
        self._refresh_health_panels()

    def restart_engine(self):
        if self.engine and self.engine.isRunning():
            self.engine.finished.connect(self._on_reiniciar_apos_parada)
            self.stop_engine()
        else:
            self.start_engine()

    def _on_reiniciar_apos_parada(self):
        """Sobe a engine de novo assim que a anterior terminou de se limpar.

        Roda depois do `on_engine_finished` (conectado antes, no `start_engine`), então a
        engine antiga já foi descartada. Não precisa desconectar nada: o objeto inteiro é
        jogado fora, e o novo `start_engine` cria as conexões do zero.
        """
        self.start_engine()

    def on_fps_ajustado_pela_camera(self, fps):
        """A câmera recusou o FPS pedido e caiu para outro. Alinha a UI com a realidade.

        Sem isto o usuário via o aviso no status mas o botão continuava marcando 60,
        com a interface discordando do que estava rodando. Ver D-34.

        `blockSignals` evita que corrigir o botão dispare `on_fps_changed`, que gravaria
        no config e poderia pedir restart.
        """
        self.estado.camera_fps = int(fps)

        with vinculo.sem_sinais(*self.fps_buttons.values()):
            self.geral_tab.set_fps(int(fps))

    def on_engine_finished(self):
        self.marcar_engine(EstadoEngine.PARADA)
        self.set_config_enabled(True)
        self.status_label.setText("Status: Parado")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._clear_preview()
        self.geral_tab.reset_latency_badge()
        self.engine = None
        self._refresh_health_panels()
