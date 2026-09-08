try:
    from PySide6.QtMultimedia import QMediaDevices
except Exception:
    QMediaDevices = None

try:
    from pygrabber.dshow_graph import FilterGraph  # type: ignore[import-not-found]
except Exception:
    FilterGraph = None

from core.capacidades_camera import (
    capacidades,
    fps_suportado,
    preset_recomendado,
    resolucao_suportada,
)
from ui.presets import RESOLUTION_PRESETS, RESOLUTION_PRESETS_REVERSED
from util.logger import get_logger

logger = get_logger(__name__)


class CameraMixin:

    @staticmethod
    def _is_virtual_camera_name(name):
        value = (name or "").strip().lower()
        virtual_tokens = (
            "obs virtual",
            "virtual camera",
            "vcam",
            "xsplit",
            "manycam",
            "snap camera",
        )
        return any(token in value for token in virtual_tokens)

    def _normalize_camera_display_name(self, name, index):
        clean_name = (name or "").strip()
        if self._is_virtual_camera_name(clean_name):
            return "OBS Virtual Camera"
        if clean_name:
            return clean_name
        return f"Câmera {index}"

    @staticmethod
    def _dshow_device_names():
        if FilterGraph is None:
            return []
        try:
            graph = FilterGraph()
            return list(graph.get_input_devices() or [])
        except Exception as exc:
            logger.debug("Falha ao listar dispositivos DirectShow: %s", exc)
            return []

    def _populate_camera_devices(self):
        self.camera_device_combo.blockSignals(True)
        self.camera_device_combo.clear()

        camera_cfg = self.config.setdefault("camera", {})
        selected_index = int(camera_cfg.get("index", 0))
        selected_name = str(camera_cfg.get("device_name", "") or "").strip()

        # Preferir QMediaDevices (rápido, sem cv2)
        raw_names = []
        if QMediaDevices is not None:
            try:
                raw_names = [d.description() for d in QMediaDevices.videoInputs()]
            except Exception as exc:
                logger.debug("Falha ao listar via QMediaDevices: %s", exc)

        # Fallback: pygrabber DirectShow
        if not raw_names:
            raw_names = self._dshow_device_names()

        camera_entries = []
        if raw_names:
            for index, name in enumerate(raw_names):
                display_name = self._normalize_camera_display_name(name, index)
                camera_entries.append((display_name, index))
        else:
            camera_entries = [(selected_name or "Câmera 0", 0)]

        camera_entries.sort(key=lambda item: (self._is_virtual_camera_name(item[0]), item[1]))

        for name, index in camera_entries:
            self.camera_device_combo.addItem(name, index)

        selected_pos = 0
        for pos in range(self.camera_device_combo.count()):
            if int(self.camera_device_combo.itemData(pos)) == selected_index:
                selected_pos = pos
                break
        else:
            if selected_name:
                for pos in range(self.camera_device_combo.count()):
                    if self.camera_device_combo.itemText(pos).strip().lower() == selected_name.lower():
                        selected_pos = pos
                        break
                else:
                    for pos in range(self.camera_device_combo.count()):
                        if not self._is_virtual_camera_name(self.camera_device_combo.itemText(pos)):
                            selected_pos = pos
                            break
            else:
                for pos in range(self.camera_device_combo.count()):
                    if not self._is_virtual_camera_name(self.camera_device_combo.itemText(pos)):
                        selected_pos = pos
                        break

        self.camera_device_combo.setCurrentIndex(selected_pos)
        selected_data = self.camera_device_combo.currentData()
        if selected_data is not None:
            camera_cfg["index"] = int(selected_data)
        camera_cfg["device_name"] = self.camera_device_combo.currentText().strip()
        self.camera_device_combo.blockSignals(False)

    def on_camera_changed(self, _value):
        selected_index = self.camera_device_combo.currentData()
        if selected_index is None:
            selected_index = self.camera_device_combo.currentIndex()
        self.estado.camera_indice = int(selected_index)
        self.estado.camera_dispositivo = self.camera_device_combo.currentText().strip()
        self.aplicar_capacidades_da_camera()

    def on_resolution_changed(self, value):
        if value not in RESOLUTION_PRESETS:
            return
        width, height = RESOLUTION_PRESETS[value]
        self.estado.camera_largura = width
        self.estado.camera_altura = height
        # O teto de FPS varia por resolução, então a lista de FPS válidos muda junto.
        self.aplicar_capacidades_da_camera()

    def aplicar_capacidades_da_camera(self):
        """Desabilita na UI os modos que a câmera selecionada não oferece. Ver D-38.

        Consulta o DirectShow a cada chamada (~170ms) em vez de guardar cache: capacidade
        em cache envelhece mal — trocar de webcam com dado velho esconderia modos que
        funcionam — e a consulta é barata o bastante para dispensar isso.

        Se a consulta falhar, `capacidades()` devolve vazio e **tudo é reabilitado**. Um
        probe quebrado não pode trancar o usuário fora de opções que a câmera tem.
        """
        camera_cfg = self.config.setdefault("camera", {})
        modos = capacidades(camera_cfg.get("index", 0))

        for rotulo, botao in self.resolution_buttons.items():
            largura, altura = RESOLUTION_PRESETS[rotulo]
            suportada = resolucao_suportada(modos, largura, altura)
            botao.setEnabled(suportada)
            botao.setToolTip(
                "" if suportada else "Esta câmera não oferece esta resolução"
            )

        largura_atual = int(camera_cfg.get("width", 1280))
        altura_atual = int(camera_cfg.get("height", 720))

        for fps, botao in self.fps_buttons.items():
            suportado = fps_suportado(modos, largura_atual, altura_atual, fps)
            botao.setEnabled(suportado)
            botao.setToolTip(
                ""
                if suportado
                else f"Esta câmera não faz {fps} fps em {largura_atual}x{altura_atual}"
            )

        self._atualizar_aviso_de_camera(modos, largura_atual, altura_atual)

    def _atualizar_aviso_de_camera(self, modos, largura, altura):
        """Mostra a incompatibilidade numa faixa visível, não só no log. Ver D-39.

        O log serve para histórico; para uma limitação permanente da câmera ele é o lugar
        errado — some no scroll e o usuário fica tentando o mesmo valor sem entender por
        que o botão está cinza.
        """
        aviso = self.geral_tab.camera_aviso
        botao = self.geral_tab.usar_recomendado_button

        if not modos:
            aviso.setVisible(False)
            botao.setVisible(False)
            return

        problemas = []

        indisponiveis = [
            rotulo
            for rotulo, (w, h) in RESOLUTION_PRESETS.items()
            if not resolucao_suportada(modos, w, h)
        ]
        if indisponiveis:
            problemas.append("sem " + ", ".join(sorted(indisponiveis)))

        if resolucao_suportada(modos, largura, altura):
            teto = modos.get((largura, altura))
            sem_fps = [
                f for f in self.fps_buttons if not fps_suportado(modos, largura, altura, f)
            ]
            if sem_fps and teto:
                lista = "/".join(str(f) for f in sorted(sem_fps))
                problemas.append(f"máx. {int(teto)} fps em {largura}x{altura}, não {lista}")

        if not problemas:
            aviso.setVisible(False)
        else:
            # Uma linha, só o fato. O botão apagado e o tooltip já dizem o resto — repetir
            # aqui era o excesso de texto que poluía o painel. Ver D-40.
            # Sem o ⚠️: neste app ele marca falha acionável — é o mesmo glifo de "não foi
            # possível salvar as configurações". Aqui o texto é um fato do hardware, que o
            # usuário não tem como resolver. Ver D-45.
            aviso.setText("Limites desta câmera: " + " · ".join(problemas))
            aviso.setToolTip("As opções fora do alcance desta câmera ficam desabilitadas.")
            aviso.setVisible(True)

        botao.setVisible(self._preset_recomendado(modos) is not None)

    def _preset_recomendado(self, modos=None):
        """`modos` já em mãos evita um segundo probe de ~170ms no mesmo ciclo."""
        if modos is None:
            modos = capacidades(self.config.get("camera", {}).get("index", 0))
        return preset_recomendado(
            modos,
            self.config.get("modo", "automatico"),
            list(RESOLUTION_PRESETS.values()),
            sorted(self.fps_buttons),
        )

    def aplicar_preset_recomendado(self):
        """Aplica o melhor modo para o modo de operação atual. Ver D-39."""
        preset = self._preset_recomendado()
        if preset is None:
            self._append_log("Não foi possível recomendar uma configuração para esta câmera.")
            return

        largura, altura, fps = preset
        camera_cfg = self.config.setdefault("camera", {})
        camera_cfg["width"] = int(largura)
        camera_cfg["height"] = int(altura)
        camera_cfg["fps"] = int(fps)

        rotulo = RESOLUTION_PRESETS_REVERSED.get((largura, altura))
        for botoes, alvo in (
            (self.resolution_buttons, rotulo),
            (self.fps_buttons, int(fps)),
        ):
            for chave, botao in botoes.items():
                botao.blockSignals(True)
                botao.setChecked(chave == alvo)
                botao.blockSignals(False)

        motivo = (
            "a imagem vai para o OBS, então vale a maior resolução"
            if self.config.get("modo") == "automatico"
            else "sem câmera virtual, acima de 720p não melhora a detecção e só custa CPU"
        )
        self._append_log(f"Configuração recomendada: {largura}x{altura} a {fps} fps — {motivo}.")

        self.aplicar_capacidades_da_camera()
        self.salvar_config_automatico()

        if self.engine and self.engine.isRunning():
            self._append_log("Reinicie a captura para a nova resolução valer.")

    def on_fps_changed(self, value):
        self.estado.camera_fps = int(value)
