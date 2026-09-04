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
from core.modos import migrar_modo
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
        
        # Check 2: rejeita aceleração brusca (ver _sem_aceleracao_brusca)
        sem_arranco = True
        if self.check_velocity and len(self.movement_history) >= 3:
            sem_arranco = self._sem_aceleracao_brusca()

        return meets_frame_requirement and sem_arranco

    def _sem_aceleracao_brusca(self):
        """
        Rejeita apenas quem está acelerando de forma brusca nos últimos 3 frames.

        ATENÇÃO — o nome antigo (`_is_movement_decreasing`) prometia mais do que este
        método entrega, e por isso foi trocado. Ele NÃO exige desaceleração: aceita
        movimento que *aumentou*, desde que o aumento seja menor que metade do
        `motion_threshold` (com o default de 4px, tolera crescer até 2px). Na prática é
        um filtro de arranco, e o trabalho pesado de exigir mão parada é do
        `stable_frame_count`.

        Endurecer isso para exigir desaceleração de verdade mudaria quando os gestos
        disparam e precisa de validação com câmera real — é decisão de comportamento,
        não limpeza. Ver B-06 no backlog.

        Returns:
            bool: True se não houve aceleração brusca no intervalo observado
        """
        if len(self.movement_history) < 3:
            return True

        # Pegar últimos 3 valores
        recent = list(self.movement_history)[-3:]

        # Calcular tendência: positivo = movimento aumentando
        velocity_trend = recent[-1] - recent[0]
        
        # Passa se diminuiu (negativo), ficou estável (~0), ou cresceu pouco.
        # Só reprova o arranco: crescimento acima de metade do motion_threshold.
        tolerancia_de_crescimento = self.motion_threshold * 0.5

        return velocity_trend <= tolerancia_de_crescimento

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
    latency_updated = Signal(float)  # ms médio a cada 30 frames

    def __init__(self, config):
        super().__init__()

        self.config = config
        self.running = False
        self._preview_suprimido = False
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
        self.modo = migrar_modo(self.config.get("modo"))

        camera_cfg = self.config.get("camera", {})
        gestures_cfg = self.config.get("gestures", {})
        self.show_skeleton = bool(camera_cfg.get("show_skeleton", True))
        # Independente do preview: o que o público vê no OBS é escolha separada do que o
        # streamer vê para calibrar. Default False — esqueleto não vaza para a live.
        self.skeleton_na_vcam = bool(camera_cfg.get("skeleton_na_vcam", False))

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

        # Stability monitoring - garante que mão está parada antes de executar gesto
        self.stability_enabled = gestures_cfg.get("enable_stability_check", True)
        _stability_kwargs = dict(
            motion_threshold=float(gestures_cfg.get("motion_pixel_threshold", 4)),
            stability_min_frames=int(gestures_cfg.get("stability_min_frames", 3)),
            check_velocity=gestures_cfg.get("check_velocity_trend", True),
        )
        _window_maxlen = max(3, self.detection_window_size)
        # Estado per-hand: detection_window, stability_monitor, gesto_ativo, inicio_gesto
        self._hand_states = {
            hand_id: {
                "detection_window": deque(maxlen=_window_maxlen),
                "stability_monitor": GestureStabilityMonitor(**_stability_kwargs),
                "gesto_ativo": None,
                "inicio_gesto": None,
            }
            for hand_id in ("Left", "Right")
        }

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
            camera_name=camera_cfg.get("device_name", ""),
            width=camera_cfg.get("width", 1920),
            height=camera_cfg.get("height", 1080),
            fps=camera_cfg.get("fps", 30),
            enable_virtual_camera=(self.modo == "automatico"),
            virtual_camera_device=camera_cfg.get("virtual_camera_device"),
        )

        self.process_fps = int(camera_cfg.get("process_fps", 30))
        self._frame_interval = 1.0 / max(1, self.process_fps)

        max_maos = int(self.config.get("max_maos", 1))
        self.tracker = HandTracker(max_num_hands=max_maos)
        self.detector = GestureDetector()
        self.actions = ActionManager(None, modo=self.modo)
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

    def set_preview_suprimido(self, valor: bool):
        self._preview_suprimido = bool(valor)

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

    def _get_stable_gesture(self, detection_window, raw_gesture):
        detection_window.append(raw_gesture)

        valid = [gesture for gesture in detection_window if gesture]
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

        if self.modo not in ("manual", "automatico"):
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

        try:
            self.camera.iniciar()
        except Exception as exc:
            logger.exception("Falha ao iniciar câmera: %s", exc)
            self.status_changed.emit("Falha ao iniciar câmera")
            self.running = False
            return

        if not self.camera.aberta:
            self.status_changed.emit("Falha ao iniciar câmera")
            self.running = False
            return

        self.status_changed.emit("Câmera iniciada")

        if self.modo == "teste":
            self.status_changed.emit("Modo Teste — ações desativadas")

        ultimo_disparo_por_gesto = {}
        _latency_count = 0
        _latency_sum = 0.0

        try:
            while self.running:
                _loop_start = time.monotonic()
                try:
                    ok, frame = self.camera.ler_frame()
                    if not ok:
                        time.sleep(0.01)
                        continue

                    _proc_start = time.monotonic()
                    # frame_nativo preserva a resolução de captura. processar() devolve a
                    # versão reduzida da inferência, que serve ao preview mas seria um
                    # upscale borrado se fosse parar na câmera virtual.
                    frame_nativo = frame
                    frame_preview, maos = self.tracker.processar(
                        frame, draw_skeleton=self.show_skeleton
                    )
                    tempo_atual = time.time()

                    maos_detectadas = {mao["handedness"] for mao in maos}

                    # Passo 1: atualizar o estado de cada mão e colher o gesto estável.
                    # O despacho NÃO acontece aqui — precisa ver as duas mãos antes para
                    # saber qual delas começou o gesto primeiro. Ver D-31.
                    gestos_por_mao = {}
                    for mao in maos:
                        hand_id = mao["handedness"]
                        # O MediaPipe só devolve "Left"/"Right", mas indexar direto faria
                        # um label inesperado virar KeyError a cada frame, inundando o log
                        # do loop principal. Ignorar a mão é degradação preferível.
                        hand_state = self._hand_states.get(hand_id)
                        if hand_state is None:
                            logger.warning("Handedness inesperado, mão ignorada: %r", hand_id)
                            continue

                        resultado = self._atualizar_estado_da_mao(
                            hand_state, mao["landmarks"], tempo_atual
                        )
                        if resultado is not None:
                            gestos_por_mao[hand_id] = resultado

                    # Resetar estado de mãos não detectadas neste frame
                    for hand_id, hand_state in self._hand_states.items():
                        if hand_id not in maos_detectadas:
                            hand_state["gesto_ativo"] = None
                            hand_state["inicio_gesto"] = None

                    # Passo 2: uma ação por vez — a primeira mão a fazer o gesto vence.
                    # Ver D-31. Com as duas mãos em quadro fazendo gestos diferentes,
                    # disparar as duas ações quase nunca é o que o usuário quer.
                    self._despachar_primeira_mao(
                        gestos_por_mao, tempo_atual, ultimo_disparo_por_gesto
                    )

                    if self.camera.enable_virtual_camera:
                        # Câmera virtual recebe a resolução nativa. Só copia quando vai
                        # anotar — desenhar direto mutaria o frame compartilhado.
                        if self.skeleton_na_vcam and maos:
                            frame_vcam = frame_nativo.copy()
                            self.tracker.desenhar_esqueleto(frame_vcam, maos)
                        else:
                            frame_vcam = frame_nativo
                        self.camera.enviar_para_virtual(frame_vcam)
                    if not self._preview_suprimido:
                        self.frame_ready.emit(frame_preview)

                    _latency_sum += (time.monotonic() - _proc_start) * 1000
                    _latency_count += 1
                    if _latency_count >= 30:
                        self.latency_updated.emit(_latency_sum / _latency_count)
                        _latency_sum = 0.0
                        _latency_count = 0

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

    def _atualizar_estado_da_mao(self, hand_state, pontos, tempo_atual):
        """Avança o estado de uma mão e devolve `(gesto, estavel, inicio)` ou `None`.

        `None` quando não há gesto estável — o estado da mão é zerado nesse caso.
        """
        raw_gesture = self._normalize_gesture_name(self.detector.detectar(pontos))
        gesto = self._get_stable_gesture(hand_state["detection_window"], raw_gesture)

        if not gesto:
            hand_state["gesto_ativo"] = None
            hand_state["inicio_gesto"] = None
            return None

        if hand_state["gesto_ativo"] != gesto:
            hand_state["inicio_gesto"] = tempo_atual
            hand_state["gesto_ativo"] = gesto
            hand_state["stability_monitor"].reset()

        is_stable = True
        if self.stability_enabled:
            is_stable = hand_state["stability_monitor"].update(pontos)

        return (gesto, is_stable, hand_state["inicio_gesto"])

    def _resolver_binding(self, gesto):
        """Config de um gesto individual, com fallback para o `scene_map` legado."""
        cfg = self.gesture_bindings.get(gesto, {})
        if cfg:
            return cfg

        nome_cena_legado = self.mapa_cenas.get(gesto, "")
        if not nome_cena_legado:
            return {}

        return {
            "enabled": True,
            "hold_time": self.tempo_minimo,
            "cooldown": self.cooldown,
            "scene": nome_cena_legado,
            "play_sound": False,
            "sound_file": "",
            "hotkey": "",
        }

    def _despachar_primeira_mao(self, gestos_por_mao, tempo_atual, ultimo_disparo_por_gesto):
        """Dispara no máximo UMA ação: a da mão que começou o gesto primeiro. Ver D-31.

        Duas mãos são rastreadas para que ter as duas em quadro não atrapalhe — o usuário
        não precisa esconder uma nem se preocupar com qual é a "mão certa". Mas a ação
        continua sendo de uma mão só: disparar duas cenas porque as duas mãos fizeram
        gestos diferentes quase nunca é o que se quer numa live.

        Critério de desempate: o menor `inicio` de gesto, ou seja, quem está segurando o
        gesto há mais tempo. Determinístico e não depende da ordem em que o MediaPipe
        devolveu as mãos.
        """
        if not gestos_por_mao:
            return

        candidatos = []
        for gesto, is_stable, inicio in gestos_por_mao.values():
            cfg = self._resolver_binding(gesto)
            if not cfg or not cfg.get("enabled", True):
                continue
            candidatos.append((inicio or tempo_atual, gesto, cfg, is_stable))

        if not candidatos:
            return

        candidatos.sort(key=lambda item: item[0])
        inicio, gesto, cfg, is_stable = candidatos[0]

        self._tentar_disparar(
            gesto, cfg, inicio, is_stable, tempo_atual, ultimo_disparo_por_gesto
        )

    def _tentar_disparar(self, nome, cfg, inicio, estavel, tempo_atual, ultimo_disparo_por_gesto):
        """Dispara a ação se o hold completou, a mão está estável e o cooldown passou."""
        if not cfg or not inicio or not estavel:
            return

        hold_time = float(cfg.get("hold_time", self.tempo_minimo))
        if (tempo_atual - inicio) < hold_time:
            return

        cooldown = float(cfg.get("cooldown", self.cooldown))
        if (tempo_atual - ultimo_disparo_por_gesto.get(nome, 0.0)) <= cooldown:
            return

        action_submitted = False

        if self.actions and self.modo != "teste":
            try:
                scene = cfg.get("scene", "").strip()
                use_scene = bool(cfg.get("use_scene", bool(scene)))
                use_sound = bool(
                    cfg.get("use_sound", bool(cfg.get("play_sound", False)))
                )
                hotkey = cfg.get("hotkey", "").strip()
                use_hotkey = bool(cfg.get("use_hotkey", bool(hotkey)))

                if self.action_future and not self.action_future.done():
                    self.status_changed.emit("Aguardando ação anterior")
                else:
                    self.action_future = self.action_executor.submit(
                        self._executar_acoes_gesto,
                        use_scene,
                        scene,
                        use_sound,
                        cfg.get("sound_file", "").strip(),
                        use_hotkey,
                        hotkey,
                    )
                    action_submitted = True

                status_parts = [f"Gesto {nome}"]
                if use_scene and scene:
                    status_parts.append(f"cena {scene}")
                if use_sound and cfg.get("sound_file", "").strip():
                    status_parts.append("som")
                if use_hotkey and hotkey:
                    status_parts.append(f"atalho {hotkey}")

                if len(status_parts) == 1:
                    self.status_changed.emit(f"{status_parts[0]} acionado")
                else:
                    self.status_changed.emit(
                        ": ".join([status_parts[0], ", ".join(status_parts[1:])])
                    )
            except Exception as exc:
                logger.exception("Erro ao executar ação: %s", exc)

        elif self.modo == "teste":
            self.status_changed.emit(
                f"Gesto detectado: {nome} (Modo Teste — ação bloqueada)"
            )
            action_submitted = True

        if action_submitted:
            ultimo_disparo_por_gesto[nome] = tempo_atual

    def _executar_acoes_gesto(self, use_scene, scene, use_sound, sound_file, use_hotkey, hotkey):
        if not self.actions:
            return

        if use_scene and scene:
            self.actions.executar("trocar_cena", scene)

        if use_sound and sound_file:
            self.actions.executar("tocar_som", sound_file)

        if use_hotkey and hotkey:
            self.actions.executar("atalho", hotkey)
            self.status_changed.emit(f"Hotkey enviada: {hotkey}")

    def set_obs_controller(self, obs_controller):
        """Troca atômica do OBSController. Chamado pela thread da UI via sinal."""
        self.obs = obs_controller
        if self.actions:
            self.actions.obs = obs_controller

    def stop(self):
        """Sinaliza parada e espera a thread encerrar de fato.

        O timeout precisa cobrir o pior caso do `CameraManager.encerrar()` (1.5s + 2s de
        join, mais o fechamento da câmera virtual). Com os 2s anteriores o `wait` estourava
        no meio da limpeza e `stop()` retornava com a câmera ainda presa — o `iniciar()`
        seguinte então falhava com `[Errno 5] I/O error`.

        O retorno do `wait` também era ignorado, então nada indicava que a parada tinha
        falhado. Agora falha ruidosa: quem chama decide o que fazer, e o log diz o motivo.
        """
        self.running = False
        if not self.isRunning():
            return True

        parou = self.wait(8000)
        if not parou:
            logger.error(
                "Engine não encerrou em 8s — a câmera pode continuar ocupada e a "
                "próxima inicialização falhar"
            )
        return parou
