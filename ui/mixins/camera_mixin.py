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
    resolucao_suportada,
)
from ui.presets import RESOLUTION_PRESETS
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
        camera_cfg = self.config.setdefault("camera", {})
        camera_cfg["index"] = int(selected_index)
        camera_cfg["device_name"] = self.camera_device_combo.currentText().strip()
        self.aplicar_capacidades_da_camera()
        self.salvar_config_automatico()

    def on_resolution_changed(self, value):
        if value not in RESOLUTION_PRESETS:
            return
        width, height = RESOLUTION_PRESETS[value]
        self.config.setdefault("camera", {})["width"] = width
        self.config.setdefault("camera", {})["height"] = height
        # O teto de FPS varia por resolução, então a lista de FPS válidos muda junto.
        self.aplicar_capacidades_da_camera()
        self.salvar_config_automatico()

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

        self._avisar_selecao_nao_suportada(modos, largura_atual, altura_atual)

    def _avisar_selecao_nao_suportada(self, modos, largura, altura):
        """Diz no log quando o que está configurado não existe na câmera.

        Não corrige sozinho: o FPS já tem o fallback do D-32, que ajusta na hora de abrir
        e devolve o valor real para a UI. Trocar a escolha do usuário aqui, antes mesmo de
        ele tentar iniciar, seria mexer na config dele sem que nada tivesse falhado.
        """
        if not modos:
            self._ultimo_aviso_de_capacidade = ""
            return

        aviso = ""
        if not resolucao_suportada(modos, largura, altura):
            aviso = (
                f"⚠️ A câmera selecionada não oferece {largura}x{altura}. "
                "Escolha uma resolução habilitada antes de iniciar."
            )
        else:
            fps_atual = int(self.config.get("camera", {}).get("fps", 30))
            if not fps_suportado(modos, largura, altura, fps_atual):
                teto = modos.get((largura, altura))
                aviso = (
                    f"⚠️ A câmera não faz {fps_atual} fps em {largura}x{altura} "
                    f"(máximo {int(teto)}). Ela será iniciada no FPS suportado."
                )

        # Este método roda a cada troca de câmera, resolução ou recarga da UI. Sem o
        # guarda, o mesmo aviso aparecia repetido no log — inclusive duas vezes só na
        # inicialização — e log que se repete sem motivo deixa de ser lido.
        if aviso and aviso != getattr(self, "_ultimo_aviso_de_capacidade", ""):
            self._append_log(aviso)

        self._ultimo_aviso_de_capacidade = aviso

    def on_fps_changed(self, value):
        self.config.setdefault("camera", {})["fps"] = int(value)
        self.salvar_config_automatico()
