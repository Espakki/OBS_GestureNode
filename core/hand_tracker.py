import cv2
import mediapipe as mp


# Largura de processamento fixa para MediaPipe — desacoplada da resolução de captura.
# A altura é calculada proporcionalmente a partir do frame real para preservar o
# aspect ratio e evitar distorção horizontal em câmeras 16:9 (720p/1080p).
PROCESS_W = 640


class HandTracker:

    def __init__(self):
        self.mp_maos = mp.solutions.hands
        self.mp_desenho = mp.solutions.drawing_utils

        # model_complexity=0 (lite) + min_tracking_confidence=0.5 para ganho de FPS (~40-55%)
        self.maos = self.mp_maos.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def processar(self, frame, draw_skeleton=True):
        h_orig, w_orig = frame.shape[:2]

        # Redimensionar preservando aspect ratio — normaliza custo de inferência
        # independente da câmera e elimina distorção horizontal em resoluções 16:9
        process_h = max(1, int(h_orig * PROCESS_W / w_orig))
        frame_small = cv2.resize(frame, (PROCESS_W, process_h), interpolation=cv2.INTER_AREA)

        frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        resultado = self.maos.process(frame_rgb)

        pontos = []

        if resultado.multi_hand_landmarks:
            for hand_landmarks in resultado.multi_hand_landmarks:
                # Calcular landmarks na escala do frame reduzido (NÃO da resolução nativa)
                for id, lm in enumerate(hand_landmarks.landmark):
                    px = int(lm.x * PROCESS_W)
                    py = int(lm.y * process_h)
                    pontos.append((px, py))

                if draw_skeleton:
                    # Desenhar skeleton em frame_small (mesmo frame processado)
                    self.mp_desenho.draw_landmarks(
                        frame_small,
                        hand_landmarks,
                        self.mp_maos.HAND_CONNECTIONS
                    )

        return frame_small, pontos