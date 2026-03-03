import time
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QThread, Signal

from core.hand_tracker import HandTracker
from core.gesture_detector import GestureDetector
from core.camera import CameraManager
from actions.action_manager import ActionManager
from integrations.obs_controller import OBSController
from util.logger import get_logger


logger = get_logger(__name__)


GESTURE_ALIASES = {
    "JOIHA": "THUMBS_UP",
    "MÃO_ABERTA": "OPEN_HAND",
    "MAO_ABERTA": "OPEN_HAND",
    "SOCO": "FIST",
    "APONTANDO_CIMA": "POINT",
}


class GestureEngine(QThread):

    frame_ready = Signal(object)
    status_changed = Signal(str)

    def __init__(self, config):
        super().__init__()

        self.config = config
        self.running = False
        self.camera = None
        self.tracker = None
        self.detector = None
        self.obs = None
        self.actions = None
        self.action_executor = None
        self.action_future = None

        self._setup()

    def _setup(self):
        camera_cfg = self.config.get("camera", {})
        gestures_cfg = self.config.get("gestures", {})
        self.show_skeleton = bool(camera_cfg.get("show_skeleton", True))

        self.tempo_minimo = gestures_cfg.get(
            "default_hold_time",
            gestures_cfg.get("hold_time", 0.7),
        )
        self.cooldown = gestures_cfg.get(
            "default_cooldown",
            gestures_cfg.get("cooldown", 2),
        )
        self.gesture_bindings = gestures_cfg.get("bindings", {})
        self.mapa_cenas = gestures_cfg.get("scene_map", {})
        self._normalize_gesture_keys()

        self.detection_window_size = int(gestures_cfg.get("detection_window_size", 5))
        self.detection_min_hits = int(gestures_cfg.get("detection_min_hits", 3))
        self.detection_window = deque(maxlen=max(3, self.detection_window_size))

        if not self.gesture_bindings and self.mapa_cenas:
            self.gesture_bindings = {
                gesture: {
                    "enabled": True,
                    "hold_time": self.tempo_minimo,
                    "cooldown": self.cooldown,
                    "scene": scene,
                    "play_sound": False,
                    "sound_file": "",
                    "hotkey": "",
                }
                for gesture, scene in self.mapa_cenas.items()
            }

        self.camera = CameraManager(
            camera_index=camera_cfg.get("index", 0),
            width=camera_cfg.get("width", 1280),
            height=camera_cfg.get("height", 720),
            fps=camera_cfg.get("fps", 30),
            enable_virtual_camera=camera_cfg.get("enable_virtual_camera"),
            virtual_camera_device=camera_cfg.get("virtual_camera_device"),
        )

        self.tracker = HandTracker()
        self.detector = GestureDetector()
        self.actions = ActionManager(None)
        self.action_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gesture-actions")

    def _normalize_gesture_name(self, gesture_name):
        if not gesture_name:
            return gesture_name
        return GESTURE_ALIASES.get(gesture_name, gesture_name)

    def _normalize_gesture_keys(self):
        if isinstance(self.gesture_bindings, dict):
            normalized_bindings = {}
            for gesture_name, config in self.gesture_bindings.items():
                normalized_bindings[self._normalize_gesture_name(gesture_name)] = config
            self.gesture_bindings = normalized_bindings

        if isinstance(self.mapa_cenas, dict):
            normalized_scene_map = {}
            for gesture_name, scene_name in self.mapa_cenas.items():
                normalized_scene_map[self._normalize_gesture_name(gesture_name)] = scene_name
            self.mapa_cenas = normalized_scene_map

    def _get_stable_gesture(self, raw_gesture):
        self.detection_window.append(raw_gesture)

        valid = [gesture for gesture in self.detection_window if gesture]
        if not valid:
            return None

        counts = Counter(valid)
        top_gesture, top_hits = counts.most_common(1)[0]
        if top_hits >= self.detection_min_hits:
            return top_gesture
        return None

    def _connect_obs(self):
        self.obs = None
        if self.actions:
            self.actions.obs = None

        if self.config.get("modo") != "obs":
            return

        obs_cfg = self.config.get("obs", {})
        self.obs = OBSController(
            host=obs_cfg.get("host", "localhost"),
            port=obs_cfg.get("port", 4455),
            password=obs_cfg.get("password"),
        )

        try:
            self.obs.connect()
            if self.actions:
                self.actions.obs = self.obs
            self.status_changed.emit("OBS conectado")
        except Exception as exc:
            logger.exception("Falha ao conectar OBS: %s", exc)
            self.status_changed.emit("Falha ao conectar OBS")
            self.obs = None

    def run(self):
        self.running = True
        self.status_changed.emit("Engine iniciada")

        self._connect_obs()
        self.camera.iniciar()

        if not self.camera.capture or not self.camera.capture.isOpened():
            self.status_changed.emit("Falha ao iniciar câmera")
            self.running = False
            return

        self.status_changed.emit("Câmera iniciada")

        ultimo_disparo_por_gesto = {}
        inicio_gesto = None
        gesto_ativo = None

        try:
            while self.running:
                try:
                    ok, frame = self.camera.ler_frame()
                    if not ok:
                        time.sleep(0.01)
                        continue

                    frame, pontos = self.tracker.processar(frame, draw_skeleton=self.show_skeleton)
                    raw_gesture = self.detector.detectar(pontos)
                    raw_gesture = self._normalize_gesture_name(raw_gesture)
                    gesto = self._get_stable_gesture(raw_gesture)
                    tempo_atual = time.time()

                    if gesto:
                        if gesto_ativo != gesto:
                            inicio_gesto = tempo_atual
                            gesto_ativo = gesto

                        gesture_cfg = self.gesture_bindings.get(gesto, {})
                        if not gesture_cfg:
                            nome_cena_legado = self.mapa_cenas.get(gesto, "")
                            if nome_cena_legado:
                                gesture_cfg = {
                                    "enabled": True,
                                    "hold_time": self.tempo_minimo,
                                    "cooldown": self.cooldown,
                                    "scene": nome_cena_legado,
                                    "play_sound": False,
                                    "sound_file": "",
                                    "hotkey": "",
                                }

                        if not gesture_cfg.get("enabled", True):
                            continue

                        hold_time = float(gesture_cfg.get("hold_time", self.tempo_minimo))
                        cooldown = float(gesture_cfg.get("cooldown", self.cooldown))
                        ultimo_disparo = ultimo_disparo_por_gesto.get(gesto, 0.0)

                        if inicio_gesto and (tempo_atual - inicio_gesto) >= hold_time:
                            if (tempo_atual - ultimo_disparo) > cooldown:
                                action_submitted = False
                                nome_cena = self.mapa_cenas.get(gesto)

                                if not gesture_cfg and nome_cena:
                                    gesture_cfg = {
                                        "enabled": True,
                                        "hold_time": self.tempo_minimo,
                                        "cooldown": self.cooldown,
                                        "scene": nome_cena,
                                        "play_sound": False,
                                        "sound_file": "",
                                        "hotkey": "",
                                    }

                                if self.actions and gesture_cfg:
                                    try:
                                        scene = gesture_cfg.get("scene", "").strip()
                                        use_scene = bool(gesture_cfg.get("use_scene", bool(scene)))
                                        use_sound = bool(
                                            gesture_cfg.get(
                                                "use_sound",
                                                bool(gesture_cfg.get("play_sound", False)),
                                            )
                                        )
                                        hotkey = gesture_cfg.get("hotkey", "").strip()
                                        use_hotkey = bool(gesture_cfg.get("use_hotkey", bool(hotkey)))

                                        if self.action_future and not self.action_future.done():
                                            self.status_changed.emit("Aguardando ação anterior")
                                        else:
                                            self.action_future = self.action_executor.submit(
                                                self._executar_acoes_gesto,
                                                use_scene,
                                                scene,
                                                use_sound,
                                                gesture_cfg.get("sound_file", "").strip(),
                                                use_hotkey,
                                                hotkey,
                                            )
                                            action_submitted = True

                                        if scene:
                                            self.status_changed.emit(f"Gesto {gesto}: cena {scene}")
                                        else:
                                            self.status_changed.emit(f"Gesto {gesto} acionado")
                                    except Exception as exc:
                                        logger.exception("Erro ao executar ação: %s", exc)

                                if action_submitted:
                                    ultimo_disparo_por_gesto[gesto] = tempo_atual
                    else:
                        gesto_ativo = None
                        inicio_gesto = None

                    if self.camera.enable_virtual_camera:
                        self.camera.enviar_para_virtual(frame)
                    self.frame_ready.emit(frame)
                except Exception as exc:
                    logger.exception("Erro no loop principal: %s", exc)
                    time.sleep(0.1)
        finally:
            if self.camera:
                self.camera.encerrar()

            if self.obs:
                self.obs.disconnect()

            if self.action_executor:
                self.action_executor.shutdown(wait=False, cancel_futures=True)

            self.running = False
            self.status_changed.emit("Engine parada")

    def _executar_acoes_gesto(self, use_scene, scene, use_sound, sound_file, use_hotkey, hotkey):
        if not self.actions:
            return

        if use_scene and scene:
            self.actions.executar("trocar_cena", scene)

        if use_sound and sound_file:
            self.actions.executar("tocar_som", sound_file)

        if use_hotkey and hotkey:
            self.actions.executar("atalho", hotkey)

    def stop(self):
        self.running = False
        if self.isRunning():
            self.wait(2000)
        