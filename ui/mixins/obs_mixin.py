from core.estado_runtime import EstadoOBS
from integrations.obs_connect_thread import (
    OBSConnectThread,
    _resumir_footer_obs as _resumir_footer_obs_fn,
)
from util.logger import get_logger

logger = get_logger(__name__)


class OBSMixin:

    def on_modo_changed(self, modo):
        self.estado.modo = modo
        # A câmera virtual só existe no modo automático (D-17). Derivado, não escolhido:
        # deixar os dois separados permitia um config dizendo "manual com VCam ligada".
        self.estado.camera_virtual_ativa = modo == "automatico"
        self._refresh_health_panels()

    def on_obs_changed(self):
        self.estado.obs_host = self.obs_host.text().strip()
        self.estado.obs_porta = int(self.obs_port.value())
        self.estado.obs_senha = self.obs_password.text()

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
        self.marcar_obs(EstadoOBS.CONECTANDO)
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
        self.marcar_obs(EstadoOBS.CONECTANDO)

    def on_obs_conectado(self, obs_controller):
        self.test_obs_button.setEnabled(True)
        self.obs_status_label.setText("Status: Conectado ✅")
        self.obs_footer_label.setText("🟢 OBS: Conectado")
        if self.engine and self.engine.isRunning():
            self.engine.set_obs_controller(obs_controller)
        self.marcar_obs(EstadoOBS.CONECTADO)
        self._obs_connect_thread = None

    def on_obs_falhou(self, mensagem):
        self.test_obs_button.setEnabled(True)
        self.obs_status_label.setText(mensagem)
        self.obs_footer_label.setText(self._resumir_footer_obs(mensagem))
        self.marcar_obs(EstadoOBS.FALHOU, mensagem)
        self._obs_connect_thread = None

    def _resumir_footer_obs(self, mensagem):
        return _resumir_footer_obs_fn(mensagem)
