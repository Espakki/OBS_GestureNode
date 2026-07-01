import math
import threading
import time
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QThread, Signal

from core.hand_tracker import HandTracker
from core.gesture_detector import GestureDetector
from core.camera import CameraManager
from core.gesture_aliases import GESTURE_ALIASES
from actions.action_manager import ActionManager
from integrations.obs_controller import OBSController
from integrations.obs_connect_thread import _classificar_erro
from util.logger import get_logger


logger = get_logger(__name__)


class GestureStabilityMonitor:
    """
    Monitora a estabilidade da mão detectando movimento dos landmarks.
    
    Dois níveis de verificação:
    1. Motion Detection: Mão precisa estar parada (movimento < threshold)
    2. Velocity Check: Mão precisa estar DESACELERANDO (intenção de parada)
    
    Evita disparo acidental durante gestos naturais de conversa ou movimentação.
    """

    def __init__(self, motion_threshold=4, stability_min_frames=3, check_velocity=True):
        """
        Args:
            motion_threshold: Distância máxima em pixels que landmarks podem se mover
            stability_min_frames: Quantos frames consecutivos devem estar abaixo do threshold
            check_velocity: Se True, verifica se movimento está diminuindo (desaceleração)
        """
        self.motion_threshold = motion_threshold
        self.stability_min_frames = stability_min_frames
        self.check_velocity = check_velocity
        
        self.previous_landmarks = None
        self.stable_frame_count = 0
        
        # Histórico de movimento para velocity check
        self.movement_history = deque(maxlen=5)
        self.current_movement = 0

    def update(self, current_landmarks):
        """
        Atualiza com os landmarks atuais e retorna se mão está estável.
        
        Retorna True se:
        1. Movimento atual < motion_threshold
        2. Mantém por N frames consecutivos
        3. Se velocity check ON: movimento está diminuindo
        
        Returns:
            bool: True se mão está estável, False caso contrário
        """
        if self.previous_landmarks is None:
            self.previous_landmarks = [list(lm) for lm in current_landmarks]
            return False

        avg_movement = self._calculate_average_movement(
            self.previous_landmarks,
            current_landmarks
        )
        
        self.current_movement = avg_movement
        self.movement_history.append(avg_movement)

        # Check 1: Movimento baixo
        below_threshold = avg_movement < self.motion_threshold

        if below_threshold:
            self.stable_frame_count += 1
        else:
            self.stable_frame_count = 0

        self.previous_landmarks = [list(lm) for lm in current_landmarks]

        # Verificações finais
        meets_frame_requirement = self.stable_frame_count >= self.stability_min_frames
        
        # Check 2: Velocity check (movimento diminuindo)
        is_decelerating = True
        if self.check_velocity and len(self.movement_history) >= 3:
            is_decelerating = self._is_movement_decreasing()

        return meets_frame_requirement and is_decelerating

    def _is_movement_decreasing(self):
        """
        Verifica se movimento está diminuindo (intenção de parada).
        
        Analisa os últimos 3-5 frames para detectar tendência.
        Se velocidade está caindo, indica que usuário QUER parar a mão.
        
        Returns:
            bool: True se movimento está diminuindo ou estável (não oscilando)
        """
        if len(self.movement_history) < 3:
            return True

        # Pegar últimos 3 valores
        recent = list(self.movement_history)[-3:]
        
        # Calcular tendência
        velocity_trend = recent[-1] - recent[0]
        
        # Se está diminuindo (negativo) ou MUITO estável (próximo de 0), é bom
        # Rejeita se estava alto e subiu de novo (oscilação)
        threshold = self.motion_threshold * 0.5
        
        return velocity_trend <= threshold

    def _calculate_average_movement(self, prev_landmarks, curr_landmarks):
        """
        Calcula a distância euclidiana média entre landmarks consecutivos.
        
        Returns:
            float: Distância média em pixels
        """
        if not prev_landmarks or not curr_landmarks:
            return float('inf')

        if len(prev_landmarks) != len(curr_landmarks):
            return float('inf')

        total_distance = 0
        for prev_point, curr_point in zip(prev_landmarks, curr_landmarks):
            try:
                distance = math.hypot(
                    curr_point[0] - prev_point[0],
                    curr_point[1] - prev_point[1]
                )
                total_distance += distance
            except (TypeError, IndexError):
                return float('inf')

        avg = total_distance / len(prev_landmarks)
        return avg

    def reset(self):
        """Reseta o monitor quando gesto muda."""
        self.previous_landmarks = None
        self.stable_frame_count = 0
        self.movement_history.clear()
        self.current_movement = 0



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

        self._bindings_lock = threading.RLock()
        self._gesture_bindings = {}
        self._mapa_cenas = {}

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

        self.detection_window_size = int(gestures_cfg.get("detection_window_size", 7))
        self.detection_min_hits = int(gestures_cfg.get("detection_min_hits", 5))
        self.detection_window = deque(maxlen=max(3, self.detection_window_size))

        # Stability monitoring - garante que mão está parada antes de executar gesto
        self.stability_enabled = gestures_cfg.get("enable_stability_check", True)
        self.stability_monitor = GestureStabilityMonitor(
            motion_threshold=float(gestures_cfg.get("motion_pixel_threshold", 4)),
            stability_min_frames=int(gestures_cfg.get("stability_min_frames", 3)),
            check_velocity=gestures_cfg.get("check_velocity_trend", True)
        )

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

        self.process_fps = int(camera_cfg.get("process_fps", 30))
        self._frame_interval = 1.0 / max(1, self.process_fps)

        self.tracker = HandTracker()
        self.detector = GestureDetector()
        self.actions = ActionManager(None)
        self.action_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gesture-actions")

    @property
    def gesture_bindings(self):
        with self._bindings_lock:
            return self._gesture_bindings

    @gesture_bindings.setter
    def gesture_bindings(self, value):
        with self._bindings_lock:
            self._gesture_bindings = value or {}

    @property
    def mapa_cenas(self):
        with self._bindings_lock:
            return self._mapa_cenas

    @mapa_cenas.setter
    def mapa_cenas(self, value):
        with self._bindings_lock:
            self._mapa_cenas = value or {}

    def _normalize_gesture_name(self, gesture_name):
        if not gesture_name:
            return gesture_name
        return GESTURE_ALIASES.get(gesture_name, gesture_name)

    def _normalize_gesture_keys(self):
        # Acessa atributos privados diretamente sob RLock — evita re-aquisicao
        # reentrante via property (RLock suporta reentrada, mas e desnecessario)
        # e garante que a normalizacao de ambos os dicts seja atomica.
        with self._bindings_lock:
            if isinstance(self._gesture_bindings, dict):
                self._gesture_bindings = {
                    self._normalize_gesture_name(k): v
                    for k, v in self._gesture_bindings.items()
                }
            if isinstance(self._mapa_cenas, dict):
                self._mapa_cenas = {
                    self._normalize_gesture_name(k): v
                    for k, v in self._mapa_cenas.items()
                }

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
            mensagem = _classificar_erro(exc)
            self.status_changed.emit(f"OBS: {mensagem}")
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
                _loop_start = time.monotonic()
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
                            self.stability_monitor.reset()

                        # Atualizar monitor de estabilidade com landmarks atuais
                        is_stable = True
                        if self.stability_enabled:
                            is_stable = self.stability_monitor.update(pontos)

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

                        if inicio_gesto and (tempo_atual - inicio_gesto) >= hold_time and is_stable:
                            if (tempo_atual - ultimo_disparo) > cooldown:
                                action_submitted = False

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

                                        status_parts = [f"Gesto {gesto}"]
                                        if use_scene and scene:
                                            status_parts.append(f"cena {scene}")
                                        if use_sound and gesture_cfg.get("sound_file", "").strip():
                                            status_parts.append("som")
                                        if use_hotkey and hotkey:
                                            status_parts.append(f"atalho {hotkey}")

                                        if len(status_parts) == 1:
                                            self.status_changed.emit(f"{status_parts[0]} acionado")
                                        else:
                                            self.status_changed.emit(": ".join([status_parts[0], ", ".join(status_parts[1:])]))
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
                    elapsed = time.monotonic() - _loop_start
                    sleep_time = self._frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
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

    def set_obs_controller(self, obs_controller):
        """Troca atômica do OBSController. Chamado pela thread da UI via sinal."""
        self.obs = obs_controller
        if self.actions:
            self.actions.obs = obs_controller

    def stop(self):
        self.running = False
        if self.isRunning():
            self.wait(2000)
