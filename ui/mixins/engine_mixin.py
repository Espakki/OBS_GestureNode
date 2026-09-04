import os

from PySide6.QtWidgets import QMessageBox

from engine.gesture_engine import GestureEngine
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

        self.config["max_maos"] = max_maos
        self.salvar_config_automatico()

        if self.engine and self.engine.isRunning():
            self.restart_engine()

    def _reverter_selecao_de_maos(self, valor):
        """Devolve os botões ao estado anterior sem disparar o handler de novo."""
        for botao in (self.maos_1_button, self.maos_2_button):
            botao.blockSignals(True)
        try:
            self.geral_tab.set_max_maos(valor)
        finally:
            for botao in (self.maos_1_button, self.maos_2_button):
                botao.blockSignals(False)

    def start_engine(self):
        erros, avisos = self._validar_config_execucao()

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
        self.engine.start()

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
        self.status_label.setText("Status: Parando...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

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
        self.config.setdefault("camera", {})["fps"] = int(fps)
        self.salvar_config_automatico()

        for botao in self.fps_buttons.values():
            botao.blockSignals(True)
        try:
            self.geral_tab.set_fps(int(fps))
        finally:
            for botao in self.fps_buttons.values():
                botao.blockSignals(False)

    def on_engine_finished(self):
        self.set_config_enabled(True)
        self.status_label.setText("Status: Parado")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._clear_preview()
        self.geral_tab.reset_latency_badge()
        self.engine = None
        self._refresh_health_panels()

    def _validar_config_execucao(self):
        erros = []
        avisos = []

        modo = self.config.get("modo", "automatico")
        obs_cfg = self.config.get("obs", {})
        bindings = self.config.get("gestures", {}).get("bindings", {})
        active_set = set(self._active_gestures())

        if modo in ("manual", "automatico"):
            if not str(obs_cfg.get("host", "")).strip():
                erros.append("Host do OBS está vazio")
            porta = int(obs_cfg.get("port", 0) or 0)
            if porta <= 0:
                erros.append("Porta do OBS inválida")

        gestos_ativos = [
            (nome, cfg)
            for nome, cfg in bindings.items()
            if nome in active_set
        ]

        if not gestos_ativos:
            avisos.append("Nenhum gesto está ativado")

        tem_alguma_acao = False
        for nome, cfg in gestos_ativos:
            usa_cena = bool(cfg.get("use_scene", False))
            usa_som = bool(cfg.get("use_sound", False))
            usa_atalho = bool(cfg.get("use_hotkey", False))

            if not (usa_cena or usa_som or usa_atalho):
                avisos.append(f"Gesto {nome} está ativo, mas sem funcionalidade selecionada")
                continue

            tem_alguma_acao = True

            if usa_cena and not str(cfg.get("scene", "")).strip():
                erros.append(f"Gesto {nome}: cena está vazia")

            if usa_som:
                arquivo_som = str(cfg.get("sound_file", "")).strip()
                if not arquivo_som:
                    erros.append(f"Gesto {nome}: arquivo de som está vazio")
                elif not os.path.exists(arquivo_som):
                    avisos.append(f"Gesto {nome}: arquivo de som não encontrado no caminho informado")

            if usa_atalho and not str(cfg.get("hotkey", "")).strip():
                avisos.append(f"Gesto {nome}: atalho está vazio")

            hold_time = float(cfg.get("hold_time", 0.7))
            cooldown = float(cfg.get("cooldown", 2.0))
            if hold_time < 0.1:
                erros.append(f"Gesto {nome}: tempo de resposta deve ser >= 0.1s")
            if cooldown < 0:
                erros.append(f"Gesto {nome}: cooldown não pode ser negativo")

        if not tem_alguma_acao and gestos_ativos:
            avisos.append("Nenhum gesto ativo possui ação efetiva")

        return erros, avisos
