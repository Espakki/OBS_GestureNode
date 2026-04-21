import math

class GestureDetector:
    GESTURE_ALIASES = {
        "THUMBS_UP": "Joinha",
        "THUMBS_DOWN": "Deslike",
        "OPEN_HAND": "Mão aberta",
        "FIST": "Punho",
        "POINT": "Apontando p/ cima",
        "ROCK": "ROCK",
        "THREE": "TRES",
        "FOUR": "QUATRO",
        "OK_SIGN": "OK",
        "CALL_ME": "Me liga",
    }

    def distancia(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.hypot(x2 - x1, y2 - y1)

    def _palm_size(self, points):
        return max(1.0, self.distancia(points[0], points[9]))

    def _finger_extended(self, points, tip_idx, mcp_idx):
        wrist = points[0]
        dist_tip = self.distancia(wrist, points[tip_idx])
        dist_mcp = self.distancia(wrist, points[mcp_idx])
        
        return dist_tip > (dist_mcp * 1.2)

    def detectar(self, pontos):
        if len(pontos) != 21:
            return None

        palm_size = self._palm_size(pontos)

        index_up = self._finger_extended(pontos, 8, 5)
        middle_up = self._finger_extended(pontos, 12, 9)
        ring_up = self._finger_extended(pontos, 16, 13)
        pinky_up = self._finger_extended(pontos, 20, 17)

        dist_thumb_index_base = self.distancia(pontos[4], pontos[5])
        thumb_open = dist_thumb_index_base > (palm_size * 0.6)

        thumb_up = thumb_open and (pontos[4][1] < pontos[3][1]) and (pontos[4][1] < pontos[5][1])
        thumb_down = thumb_open and (pontos[4][1] > pontos[3][1]) and (pontos[4][1] > pontos[5][1])

        thumb_index_close = self.distancia(pontos[4], pontos[8]) < (palm_size * 0.3)
        if thumb_index_close and not index_up:
            if middle_up and ring_up and pinky_up:
                return "OK_SIGN"

        if index_up and middle_up and (not ring_up) and (not pinky_up):
            if self.distancia(pontos[8], pontos[12]) < (palm_size * 0.25):
                return "Escoteiro"
            return "V"

        if thumb_open and pinky_up and (not index_up) and (not middle_up) and (not ring_up):
            return "CALL_ME"

        if middle_up and (not index_up) and (not ring_up) and (not pinky_up):
            return "Dedo do Meio"

        if index_up and pinky_up and (not middle_up) and (not ring_up):
            return "ROCK"

        if index_up and middle_up and ring_up and pinky_up:
            if thumb_open:
                return "OPEN_HAND"
            else:
                return "FOUR"

        if index_up and middle_up and ring_up and (not pinky_up):
            return "THREE"

        if index_up and (not middle_up) and (not ring_up) and (not pinky_up):
            if thumb_open:
                return "Arminha"
            else:
                return "POINT"

        if (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up):
            if thumb_up:
                return "THUMBS_UP"
            elif thumb_down:
                return "THUMBS_DOWN"
            elif not thumb_open:
                return "FIST"

        return None