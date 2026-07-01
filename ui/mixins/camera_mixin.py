import cv2

try:
    from PySide6.QtMultimedia import QMediaDevices
except Exception:
    QMediaDevices = None

try:
    from pygrabber.dshow_graph import FilterGraph  # type: ignore[import-not-found]
except Exception:
    FilterGraph = None

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
    def _probe_opencv_camera_indexes(max_devices=10):
        import sys
        from io import StringIO

        available_indexes = []

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            for index in range(max_devices):
                capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if not capture or not capture.isOpened():
                    if capture:
                        capture.release()
                    continue

                ok, _ = capture.read()
                capture.release()
                if ok:
                    available_indexes.append(index)
        finally:
            sys.stderr = old_stderr

        return available_indexes

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

        available_indexes = self._probe_opencv_camera_indexes()
        if not available_indexes:
            available_indexes = [0]

        dshow_names = self._dshow_device_names()
        qt_names = []
        if QMediaDevices is not None:
            try:
                qt_names = [device.description() for device in QMediaDevices.videoInputs()]
            except Exception as exc:
                logger.debug("Falha ao listar dispositivos de vídeo no Qt: %s", exc)

        camera_entries = []
        for index in available_indexes:
            name = ""
            if index < len(dshow_names):
                name = dshow_names[index]
            elif index < len(qt_names):
                name = qt_names[index]
            name = self._normalize_camera_display_name(name, index)

            camera_entries.append((name, index))

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
        self.salvar_config_automatico()

    def on_resolution_changed(self, value):
        if value not in RESOLUTION_PRESETS:
            return

        width, height = RESOLUTION_PRESETS[value]

        self.config.setdefault("camera", {})["width"] = width
        self.config.setdefault("camera", {})["height"] = height
        self.salvar_config_automatico()

    def on_fps_changed(self, value):
        self.config.setdefault("camera", {})["fps"] = int(value)
        self.salvar_config_automatico()
