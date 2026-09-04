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

    def _estilo_para(self, largura):
        """Espessura de traço proporcional à largura do frame.

        O padrão do MediaPipe é `DrawingSpec(thickness=2, circle_radius=2)` — **fixo em
        pixels**. Uma linha de 2px ocupa 0.31% da largura num frame de 640, mas só 0.10%
        num de 1920: três vezes mais fina. Na saída para o OBS isso aparecia como se a
        imagem estivesse esticada, quando na verdade o frame nativo estava correto e só o
        traço não acompanhava a escala. Ver D-33.

        `PROCESS_W` é a referência porque é nela que a espessura 2 foi calibrada.
        """
        escala = max(1, round(largura / PROCESS_W))
        return self.mp_desenho.DrawingSpec(
            thickness=2 * escala,
            circle_radius=2 * escala,
        )

    def desenhar_esqueleto(self, frame, maos):
        """Desenha o esqueleto das mãos em um frame de QUALQUER resolução, in-place.

        Os landmarks do MediaPipe são normalizados (0..1), então o desenho independe do
        tamanho do frame — o mesmo resultado de `processar()` serve tanto para o preview
        reduzido quanto para o frame nativo que vai para a câmera virtual. O que NÃO é
        normalizado é a espessura do traço, daí o `_estilo_para`.

        Só funciona com dicts vindos de `processar()`, que carregam `_mp_landmarks`.
        """
        if not maos:
            return

        estilo = self._estilo_para(frame.shape[1])

        for mao in maos:
            mp_landmarks = mao.get("_mp_landmarks")
            if mp_landmarks is None:
                continue
            self.mp_desenho.draw_landmarks(
                frame,
                mp_landmarks,
                self.mp_maos.HAND_CONNECTIONS,
                estilo,
                estilo,
            )

    def processar(self, frame, draw_skeleton=True):
        """Processa o frame e retorna (frame_reduzido, list[dict]).

        O frame retornado é a versão reduzida usada na inferência (largura `PROCESS_W`) —
        NÃO é o frame de captura. Quem precisa da resolução nativa (a câmera virtual) deve
        guardar o frame original antes de chamar este método e usar `desenhar_esqueleto()`
        para anotá-lo.

        Cada dict: {"landmarks": list[tuple[int,int]], "handedness": "Left"|"Right"}
        Os landmarks estão na escala do frame reduzido. O handedness já está com inversão
        aplicada — fisicamente correto para câmera frontal. Lista vazia quando nenhuma mão
        é detectada.

        `draw_skeleton` afeta apenas o frame reduzido retornado.
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

                # _mp_landmarks: objeto normalizado do MediaPipe, guardado para permitir
                # desenhar o esqueleto em outra resolução (ver desenhar_esqueleto).
                maos.append({
                    "landmarks": pontos,
                    "handedness": physical_label,
                    "_mp_landmarks": hand_landmarks,
                })

        return frame_small, maos