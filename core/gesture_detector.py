import math


class GestureDetector:
    GESTURE_ALIASES = {
        # Mapeamento do detector (nomes em inglês/uppercase) para nomes da UI/Config (português)
        "THUMBS_UP": "Joinha",
        "THUMBS_DOWN": "Deslike",
        "OPEN_HAND": "Mão aberta",
        "FIST": "Punho",
        "POINT": "Apontando p/ cima",
        "THREE": "TRES",
        "FOUR": "QUATRO",
        "OK_SIGN": "OK",
        "CALL_ME": "Me liga",
        "PINCH": "Pinça",
        "Coração Coreano": "Coração",
    }

    def distancia(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.hypot(x2 - x1, y2 - y1)

    def _finger_up(self, points, tip_idx, pip_idx, margin=6):
        return points[tip_idx][1] < (points[pip_idx][1] - margin)

    def _thumb_extended(self, points):
        tip = points[4]
        ip = points[3]
        mcp = points[2]
        wrist = points[0]

        tip_to_wrist = self.distancia(tip, wrist)
        mcp_to_wrist = max(1.0, self.distancia(mcp, wrist))
        tip_to_ip = self.distancia(tip, ip)
        ip_to_mcp = max(1.0, self.distancia(ip, mcp))

        return tip_to_wrist > (mcp_to_wrist * 1.2) and tip_to_ip > (ip_to_mcp * 0.8)

    def _thumb_up_direction(self, points):
        thumb_tip_y = points[4][1]
        thumb_ip_y = points[3][1]
        index_mcp_y = points[5][1]
        return thumb_tip_y < thumb_ip_y and thumb_tip_y < (index_mcp_y - 10)

    def _thumb_down_direction(self, points):
        thumb_tip_y = points[4][1]
        thumb_ip_y = points[3][1]
        index_mcp_y = points[5][1]
        return thumb_tip_y > thumb_ip_y and thumb_tip_y > (index_mcp_y + 10)

    def _palm_size(self, points):
        return max(1.0, self.distancia(points[0], points[9]))

    def _is_middle_finger(self, points):
        middle_up = points[12][1] < points[10][1]
        index_folded = points[8][1] > points[6][1]
        ring_folded = points[16][1] > points[14][1]
        pinky_folded = points[20][1] > points[18][1]
        return middle_up and index_folded and ring_folded and pinky_folded

    def _is_pistol(self, points):
        palm_size = self._palm_size(points)
        index_up = points[8][1] < points[6][1]
        middle_folded = points[12][1] > points[10][1]
        ring_folded = points[16][1] > points[14][1]
        pinky_folded = points[20][1] > points[18][1]

        thumb_open = self._thumb_extended(points)
        thumb_index_dist = self.distancia(points[4], points[8])
        thumb_away = thumb_index_dist > (palm_size * 0.35)

        return index_up and thumb_open and thumb_away and middle_folded and ring_folded and pinky_folded

    def _is_spiderman(self, points):
        thumb_open = self._thumb_extended(points)
        index_up = points[8][1] < points[6][1]
        pinky_up = points[20][1] < points[18][1]
        middle_folded = points[12][1] > points[10][1]
        ring_folded = points[16][1] > points[14][1]
        return thumb_open and index_up and pinky_up and middle_folded and ring_folded

    def _is_scout(self, points):
        palm_size = self._palm_size(points)
        index_up = points[8][1] < points[6][1]
        middle_up = points[12][1] < points[10][1]
        ring_folded = points[16][1] > points[14][1]
        pinky_folded = points[20][1] > points[18][1]

        fingertips_close = self.distancia(points[8], points[12]) < (palm_size * 0.20)
        return index_up and middle_up and fingertips_close and ring_folded and pinky_folded

    def _is_korean_heart(self, points):
        palm_size = self._palm_size(points)
        thumb_index_close = self.distancia(points[4], points[8]) < (palm_size * 0.18)

        middle_folded = points[12][1] > points[10][1]
        ring_folded = points[16][1] > points[14][1]
        pinky_folded = points[20][1] > points[18][1]

        return thumb_index_close and middle_folded and ring_folded and pinky_folded

    def detectar(self, pontos):
        if len(pontos) != 21:
            return None

        index_up = self._finger_up(pontos, 8, 6)
        middle_up = self._finger_up(pontos, 12, 10)
        ring_up = self._finger_up(pontos, 16, 14)
        pinky_up = self._finger_up(pontos, 20, 18)
        thumb_open = self._thumb_extended(pontos)
        thumb_up = thumb_open and self._thumb_up_direction(pontos)
        thumb_down = thumb_open and self._thumb_down_direction(pontos)

        if self._is_scout(pontos):
            return "Escoteiro"

        if index_up and middle_up and (not ring_up) and (not pinky_up):
            return "V"

        if self._is_middle_finger(pontos):
            return "Dedo do Meio"

        if self._is_korean_heart(pontos):
            return "Coração Coreano"

        if thumb_up and (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up):
            return "THUMBS_UP"

        if thumb_down and (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up):
            return "THUMBS_DOWN"

        if index_up and middle_up and ring_up and pinky_up:
            return "OPEN_HAND"

        if (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up) and (not thumb_open):
            return "FIST"

        if self._is_pistol(pontos):
            return "Arminha"

        if index_up and (not middle_up) and (not ring_up) and (not pinky_up):
            return "POINT"

        if self._is_spiderman(pontos):
            return "Homem-Aranha"

        if index_up and pinky_up and (not middle_up) and (not ring_up):
            return "ROCK"

        if index_up and middle_up and ring_up and (not pinky_up):
            return "THREE"

        if index_up and middle_up and ring_up and pinky_up and (not thumb_open):
            return "FOUR"

        ok_dist = self.distancia(pontos[4], pontos[8])
        palm_size = max(1.0, self.distancia(pontos[0], pontos[9]))
        if ok_dist < palm_size * 0.35 and middle_up and ring_up and pinky_up:
            return "OK_SIGN"

        if thumb_open and pinky_up and (not index_up) and (not middle_up) and (not ring_up):
            return "CALL_ME"

        pinch_dist = self.distancia(pontos[4], pontos[8])
        if pinch_dist < palm_size * 0.25 and (not middle_up):
            return "PINCH"

        return None
