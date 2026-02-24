import cv2
import time
import json

from core.hand_tracker import HandTracker
from core.gesture_detector import GestureDetector
from integrations.obs_controller import OBSController
from actions.action_manager import ActionManager
from core.camera import CameraManager


def carregar_config(caminho="config.json"):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            conteudo = arquivo.read().strip()
            if not conteudo:
                return {}
            return json.loads(conteudo)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("config.json inválido, usando valores padrão.")
        return {}


config = carregar_config()

camera_cfg = config.get("camera", {})
obs_cfg = config.get("obs", {})
gestures_cfg = config.get("gestures", {})

camera = CameraManager(
    camera_index=camera_cfg.get("index", 0),
    width=camera_cfg.get("width", 1280),
    height=camera_cfg.get("height", 720),
    fps=camera_cfg.get("fps", 30),
    enable_virtual_camera=camera_cfg.get("enable_virtual_camera", True),
    virtual_camera_device=camera_cfg.get("virtual_camera_device"),
)

camera.iniciar()

tracker = HandTracker()
detector = GestureDetector()

obs = OBSController(
    host=obs_cfg.get("host", "localhost"),
    port=obs_cfg.get("port", 4455),
    password=obs_cfg.get("password", "R6n3NNtb2NbyTFjH"),
)
actions = ActionManager(obs)

ultimo_gesto = None
tempo_minimo = gestures_cfg.get("hold_time", 0.7)
cooldown = gestures_cfg.get("cooldown", 2)

mapa_cenas = gestures_cfg.get("scene_map", {"V": "wini"})

inicio_gesto = None
ultimo_disparo = 0
gesto_ativo = None

try:
    while True:

        ok, frame = camera.ler_frame()
        if not ok:
            break

        frame, pontos = tracker.processar(frame)
        gesto = detector.detectar(pontos)

        tempo_atual = time.time()

        if gesto:

            if gesto_ativo != gesto:
                inicio_gesto = tempo_atual
                gesto_ativo = gesto

            tempo_segurando = tempo_atual - inicio_gesto

            if tempo_segurando >= tempo_minimo and (tempo_atual - ultimo_disparo) > cooldown:
                print("Gesto confirmado:", gesto)

                nome_cena = mapa_cenas.get(gesto)
                if nome_cena:
                    actions.executar("trocar_cena", nome_cena)

                ultimo_disparo = tempo_atual

        else:
            gesto_ativo = None
            inicio_gesto = None

        camera.enviar_para_virtual(frame)

        if camera_cfg.get("show_preview", False):
            cv2.imshow("Gesture OBS Controller", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        if not camera_cfg.get("enable_virtual_camera", True):
            time.sleep(0.01)
finally:
    camera.encerrar()
    cv2.destroyAllWindows()