from integrations.obs_connect_thread import (
    OBSConnectThread,
    _resumir_footer_obs as _resumir_footer_obs_fn,
)
from util.logger import get_logger

logger = get_logger(__name__)


class OBSMixin:

    def on_modo_changed(self, modo):
        self.config["modo"] = modo
        self.config.setdefault("camera", {})
        self.config["camera"]["enable_virtual_camera"] = modo == "automatico"
        self._refresh_health_panels()
        self.salvar_config_automatico()

    def on_obs_changed(self):
        self.config.setdefault("obs", {})
        self.config["obs"]["host"] = self.obs_host.text().strip()
        self.config["obs"]["port"] = int(self.obs_port.value())
        self.config["obs"]["password"] = self.obs_password.text()
        self.salvar_config_automatico()

    def testar_conexao_obs(self):
        if self._obs_connect_thread is not None:
            try:
                self._obs_connect_thread.connected.disconnect()
                self._obs_connect_thread.failed.disconnect()
                self._obs_connect_thread.connecting.disconnect()
            except Exception:
                pass
            self._obs_connect_thread = None

        host = self.obs_host.text().strip()
        port = self.obs_port.value()
        password = self.obs_password.text()

        self.test_obs_button.setEnabled(False)
        self.obs_status_label.setText("Conectando...")
        self.obs_footer_label.setText("⏳ OBS: Conectando...")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        thread = OBSConnectThread(host, port, password)
        thread.connecting.connect(self.on_obs_conectando)
        thread.connected.connect(self.on_obs_conectado)
        thread.failed.connect(self.on_obs_falhou)
        thread.finished.connect(thread.deleteLater)
        self._obs_connect_thread = thread
        thread.start()

    def on_obs_conectando(self):
        self.obs_status_label.setText("Conectando...")
        self.obs_footer_label.setText("⏳ OBS: Conectando...")

    def on_obs_conectado(self, obs_controller):
        self.test_obs_button.setEnabled(True)
        self.obs_status_label.setText("Status: Conectado ✅")
        self.obs_footer_label.setText("🟢 OBS: Conectado")
        if self.engine and self.engine.isRunning():
            self.engine.set_obs_controller(obs_controller)
        self._refresh_health_panels()
        self._obs_connect_thread = None

    def on_obs_falhou(self, mensagem):
        self.test_obs_button.setEnabled(True)
        self.obs_status_label.setText(mensagem)
        self.obs_footer_label.setText(self._resumir_footer_obs(mensagem))
        self._refresh_health_panels()
        self._obs_connect_thread = None

    def _resumir_footer_obs(self, mensagem):
        return _resumir_footer_obs_fn(mensagem)
