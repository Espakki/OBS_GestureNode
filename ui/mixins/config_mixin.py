import json
import os
import tempfile
from pathlib import Path

from core.gesture_aliases import GESTURE_ALIASES
from ui.presets import RESOLUTION_PRESETS_REVERSED
from util.logger import get_logger

logger = get_logger(__name__)


class ConfigMixin:

    def _init_config_schema(self):
        _legado_map = {"test": "teste", "obs": "automatico"}
        _validos = {"teste", "manual", "automatico"}
        _raw = self.config.get("modo")
        if _raw in _legado_map:
            self.config["modo"] = _legado_map[_raw]
        elif _raw in _validos:
            pass
        else:
            self.config["modo"] = "automatico"

        self.config.setdefault("max_maos", 1)

        camera_cfg = self.config.setdefault("camera", {})
        camera_cfg.setdefault("index", 0)
        camera_cfg.setdefault("device_name", "")
        camera_cfg.setdefault("width", 1280)
        camera_cfg.setdefault("height", 720)
        camera_cfg.setdefault("fps", 30)
        camera_cfg.setdefault("process_fps", 30)
        camera_cfg.setdefault("enable_virtual_camera", False)
        camera_cfg.setdefault("virtual_camera_device", None)
        camera_cfg.setdefault("show_skeleton", True)

        self.config.setdefault("onboarding_done", False)

        obs_cfg = self.config.setdefault("obs", {})
        obs_cfg.setdefault("host", "localhost")
        obs_cfg.setdefault("port", 4455)
        obs_cfg.setdefault("password", "")

        gestures_cfg = self.config.setdefault("gestures", {})
        default_hold = gestures_cfg.get("default_hold_time", gestures_cfg.get("hold_time", 2.0))
        default_cooldown = gestures_cfg.get("default_cooldown", gestures_cfg.get("cooldown", 2.0))
        default_hold = max(0.5, float(default_hold))
        default_cooldown = max(2.0, float(default_cooldown))
        gestures_cfg["default_hold_time"] = default_hold
        gestures_cfg["default_cooldown"] = default_cooldown

        raw_scene_map = gestures_cfg.get("scene_map", {}) or {}
        raw_bindings = gestures_cfg.get("bindings", {}) or {}

        scene_map = {
            GESTURE_ALIASES.get(key, key): value
            for key, value in raw_scene_map.items()
        }
        bindings = {
            GESTURE_ALIASES.get(key, key): value
            for key, value in raw_bindings.items()
        }

        normalized = {}
        gesture_ids = [gesture for gesture, _ in self.ALL_GESTURES]

        active_gestures = gestures_cfg.get("active_gestures")
        if not isinstance(active_gestures, list) or not active_gestures:
            active_gestures = [
                gesture
                for gesture, cfg in bindings.items()
                if isinstance(cfg, dict) and cfg.get("enabled", True)
            ]
        if not active_gestures:
            active_gestures = [gesture_ids[0]]

        gestures_cfg["active_gestures"] = [
            gesture
            for gesture in active_gestures
            if gesture in gesture_ids
        ]
        if not gestures_cfg["active_gestures"]:
            gestures_cfg["active_gestures"] = [gesture_ids[0]]

        for gesture, _ in self.ALL_GESTURES:
            raw = bindings.get(gesture, {}) if isinstance(bindings, dict) else {}
            hold_time = float(raw.get("hold_time", gestures_cfg["default_hold_time"]))
            cooldown = float(raw.get("cooldown", gestures_cfg["default_cooldown"]))
            hold_time = max(0.5, hold_time)
            cooldown = max(2.0, cooldown)
            normalized[gesture] = {
                "enabled": bool(raw.get("enabled", gesture in gestures_cfg["active_gestures"])),
                "hold_time": hold_time,
                "cooldown": cooldown,
                "scene": str(raw.get("scene", scene_map.get(gesture, ""))).strip(),
                "play_sound": bool(raw.get("play_sound", False)),
                "sound_file": str(raw.get("sound_file", "")).strip(),
                "hotkey": str(raw.get("hotkey", "")).strip(),
                "use_scene": bool(raw.get("use_scene", bool(raw.get("scene", scene_map.get(gesture, ""))))),
                "use_sound": bool(raw.get("use_sound", bool(raw.get("play_sound", False)))),
                "use_hotkey": bool(raw.get("use_hotkey", bool(raw.get("hotkey", "")))),
            }

        gestures_cfg["bindings"] = normalized
        self._sync_scene_map_from_bindings()

    def _load_ui_from_config(self):
        camera_cfg = self.config.get("camera", {})
        obs_cfg = self.config.get("obs", {})

        self.geral_tab.set_mode(self.config.get("modo", "automatico"))
        self.geral_tab.set_max_maos(self.config.get("max_maos", 1))

        self._populate_camera_devices()
        width = int(camera_cfg.get("width", 1280))
        height = int(camera_cfg.get("height", 720))
        self.geral_tab.set_resolution(RESOLUTION_PRESETS_REVERSED.get((width, height), "720p"))
        self.geral_tab.set_fps(int(camera_cfg.get("fps", 30)))
        self.show_skeleton_checkbox.setChecked(bool(camera_cfg.get("show_skeleton", True)))
        self.obs_host.setText(obs_cfg.get("host", "localhost"))
        self.obs_port.setValue(int(obs_cfg.get("port", 4455)))
        self.obs_password.setText(obs_cfg.get("password", ""))

        self._rebuild_gesture_grid()
        self._refresh_gesture_feature_visibility()
        self._refresh_health_panels()

    def _get_current_binding(self):
        return self.config.setdefault("gestures", {}).setdefault("bindings", {}).setdefault(
            self.current_gesture,
            {
                "enabled": True,
                "hold_time": self.config["gestures"]["default_hold_time"],
                "cooldown": self.config["gestures"]["default_cooldown"],
                "scene": "",
                "play_sound": False,
                "sound_file": "",
                "hotkey": "",
                "use_scene": False,
                "use_sound": False,
                "use_hotkey": False,
            },
        )

    def _sync_scene_map_from_bindings(self):
        gestures_cfg = self.config.setdefault("gestures", {})
        bindings = gestures_cfg.setdefault("bindings", {})
        gestures_cfg["scene_map"] = {
            gesture: cfg.get("scene", "")
            for gesture, cfg in bindings.items()
            if cfg.get("scene", "")
        }

    def salvar_config(self):
        self.salvar_config_automatico()
        self.status_label.setText("Config salva!")

    def salvar_config_automatico(self):
        self._save_timer.start(500)

    def _do_save_config(self):
        self._sync_scene_map_from_bindings()
        try:
            dir_path = self._config_path.parent
            fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                os.replace(tmp_path, str(self._config_path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as exc:
            logger.error("Falha ao salvar configuracao: %s", exc)
