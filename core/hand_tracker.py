import cv2
import mediapipe as mp


# Largura de processamento fixa para MediaPipe — desacoplada da resolução de captura.
# A altura é calculada proporcionalmente a partir do frame real para preservar o
# aspect ratio e evitar distorção horizontal em câmeras 16:9 (720p/1080p).
PROCESS_W = 640

# MediaPipe retorna handedness invertido para frames pré-espelhados (câmera frontal):
# label "Right" no resultado = mão física esquerda do usuário. Inverter na saída.
_HANDEDNESS_INVERT = {"Left": "Right", "Right": "Left"}


class HandTracker:

    def __init__(self, max_num_hands=1):
        self.mp_maos = mp.solutions.hands
        self.mp_desenho = mp.solutions.drawing_utils

        # model_complexity=0 (lite) + min_tracking_confidence=0.5 para ganho de FPS (~40-55%)
        self.maos = self.mp_maos.Hands(
            max_num_hands=max_num_hands,
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def processar(self, frame, draw_skeleton=True):
        """Processa o frame e retorna (frame_anotado, list[dict]).

        Cada dict: {"landmarks": list[tuple[int,int]], "handedness": "Left"|"Right"}
        O handedness já está com inversão aplicada — fisicamente correto para câmera frontal.
        Lista vazia quando nenhuma mão é detectada.
        """
        h_orig, w_orig = frame.shape[:2]

        # Redimensionar preservando aspect ratio — normaliza custo de inferência
        # independente da câmera e elimina distorção horizontal em resoluções 16:9
        process_h = max(1, int(h_orig * PROCESS_W / w_orig))
        frame_small = cv2.resize(frame, (PROCESS_W, process_h), interpolation=cv2.INTER_AREA)

        frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        resultado = self.maos.process(frame_rgb)

        maos = []

        if resultado.multi_hand_landmarks and resultado.multi_handedness:
            for hand_landmarks, handedness_info in zip(
                resultado.multi_hand_landmarks, resultado.multi_handedness
            ):
                raw_label = handedness_info.classification[0].label
                physical_label = _HANDEDNESS_INVERT.get(raw_label, raw_label)

                pontos = []
                for lm in hand_landmarks.landmark:
                    px = int(lm.x * PROCESS_W)
                    py = int(lm.y * process_h)
                    pontos.append((px, py))

                if draw_skeleton:
                    self.mp_desenho.draw_landmarks(
                        frame_small,
                        hand_landmarks,
                        self.mp_maos.HAND_CONNECTIONS
                    )

                maos.append({"landmarks": pontos, "handedness": physical_label})

        return frame_small, maos