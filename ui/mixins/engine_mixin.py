import os

from PySide6.QtWidgets import QMessageBox

from engine.gesture_engine import GestureEngine
from util.logger import get_logger

logger = get_logger(__name__)


class EngineMixin:

    def on_max_maos_changed(self, max_maos):
        self.config["max_maos"] = int(max_maos)
        self.salvar_config_automatico()
        if self.engine and self.engine.isRunning():
            self.restart_engine()

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

        try:
            self.engine.finished.disconnect()
        except Exception:
            pass

        self.engine.finished.connect(self.on_engine_finished)
        self.engine.stop()

        self.status_label.setText("Status: Parado")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._refresh_health_panels()

    def restart_engine(self):
        if self.engine and self.engine.isRunning():
            self.engine.finished.connect(self._on_reiniciar_apos_parada)
            self.stop_engine()
        else:
            self.start_engine()

    def _on_reiniciar_apos_parada(self):
        try:
            self.engine.finished.disconnect(self._on_reiniciar_apos_parada)
        except Exception:
            pass
        self.start_engine()

    def on_engine_finished(self):
        self.set_config_enabled(True)
        self.status_label.setText("Status: Parado")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._clear_preview()
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
