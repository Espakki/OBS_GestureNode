"""Ponte entre a janela e o estado. Ver D-47.

Este arquivo tinha 219 linhas. As que saíram não foram apagadas — foram para `core/`:

- `_init_config_schema` (~100 linhas de schema, migração e alias) → `core/config_schema.py`
- `_do_save_config` (escrita atômica) → `core/config_store.py`
- `_get_current_binding`, `_sync_scene_map_from_bindings` → `core/estado_app.py`

Nenhuma delas tocava num widget. Estavam aqui por hábito, e o preço era não terem teste:
só rodavam se alguém abrisse a janela.

O que sobrou é o que de fato é da UI: refletir o estado nos widgets, e avisar o usuário
quando o disco recusa a gravação.
"""

from PySide6.QtWidgets import QMessageBox

from core import config_store
from ui.presets import RESOLUTION_PRESETS_REVERSED
from util.logger import get_logger

logger = get_logger(__name__)


class ConfigMixin:

    def _ao_mudar_estado(self, campo, valor):
        """Assinado UMA vez, no boot. Substitui as 14 chamadas manuais de save.

        Antes, salvar dependia de cada handler lembrar de pedir. Quatorze lugares
        lembravam; os que não lembrassem perdiam a alteração em silêncio, e não havia como
        descobrir isso a não ser fechando o app e reabrindo.
        """
        self._save_timer.start(500)

    def _load_ui_from_config(self):
        """Reflete o estado nos widgets. Sentido único: estado → tela."""
        estado = self.estado

        self.geral_tab.set_mode(estado.modo)
        self.geral_tab.set_max_maos(estado.max_maos)

        self._populate_camera_devices()

        resolucao = RESOLUTION_PRESETS_REVERSED.get(
            (estado.camera_largura, estado.camera_altura), "720p"
        )
        self.geral_tab.set_resolution(resolucao)
        self.geral_tab.set_fps(estado.camera_fps)
        self.geral_tab.set_esqueleto(estado.mostrar_esqueleto, estado.esqueleto_na_vcam)

        # A aba OBS lê as credenciais do estado por ligação; nada a empurrar aqui.

        # Depois de os botões refletirem o estado, filtra o que a câmera não oferece.
        self.aplicar_capacidades_da_camera()

        self._rebuild_gesture_grid()
        self._refresh_gesture_feature_visibility()
        self._refresh_health_panels()

    def salvar_config(self):
        self.salvar_config_automatico()
        self.status_label.setText("Config salva!")

    def salvar_config_automatico(self):
        self._save_timer.start(500)

    def _do_save_config(self):
        try:
            config_store.salvar(self.estado.config_bruta(), self._config_path)
        except config_store.FalhaAoSalvar as falha:
            self._avisar_falha_de_save(falha.causa)

    def _avisar_falha_de_save(self, exc):
        """Torna visível um save que falhou, em vez de apenas registrar no log.

        Antes isto só ia para o arquivo de log: o usuário ajustava tudo, fechava o app e
        perdia as configurações sem qualquer sinal. Ver D-29.

        O diálogo aparece UMA vez por sessão. O autosave dispara a cada slider movido —
        um modal por falha seria pior que o silêncio. A status bar continua avisando
        sempre, para o caso de o usuário ter dispensado o diálogo.
        """
        if getattr(self, "status_label", None) is not None:
            self.status_label.setText("⚠️ Não foi possível salvar as configurações")

        if getattr(self, "_avisou_falha_de_save", False):
            return
        self._avisou_falha_de_save = True

        QMessageBox.warning(
            self,
            "Configurações não estão sendo salvas",
            f"Não foi possível gravar em:\n{self._config_path}\n\n"
            f"Motivo: {exc}\n\n"
            "Suas alterações valem enquanto o app estiver aberto, mas serão perdidas ao "
            "fechar. Verifique se a pasta existe e se você tem permissão de escrita nela.",
        )
