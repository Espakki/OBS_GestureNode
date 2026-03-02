import cv2
import mediapipe as mp

class HandTracker:

    def __init__(self):
        self.mp_maos = mp.solutions.hands
        self.mp_desenho = mp.solutions.drawing_utils

        self.maos = self.mp_maos.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def processar(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.maos.process(frame_rgb)

        pontos = []

        if resultado.multi_hand_landmarks:
            for hand_landmarks in resultado.multi_hand_landmarks:
                h, w, _ = frame.shape

                for id, lm in enumerate(hand_landmarks.landmark):
                    px = int(lm.x * w)
                    py = int(lm.y * h)
                    pontos.append((px, py))

                self.mp_desenho.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_maos.HAND_CONNECTIONS
                )

        return frame, pontos