import math


class GestureDetector:
    GESTURE_ALIASES = {
        "JOIHA": "THUMBS_UP",
        "MÃO_ABERTA": "OPEN_HAND",
        "MAO_ABERTA": "OPEN_HAND",
        "SOCO": "FIST",
        "APONTANDO_CIMA": "POINT",
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

    def _normalize_name(self, gesture_name):
        return self.GESTURE_ALIASES.get(gesture_name, gesture_name)

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

        if index_up and middle_up and (not ring_up) and (not pinky_up):
            return "V"

        if thumb_up and (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up):
            return "THUMBS_UP"

        if thumb_down and (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up):
            return "THUMBS_DOWN"

        if index_up and middle_up and ring_up and pinky_up:
            return "OPEN_HAND"

        if (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up) and (not thumb_open):
            return "FIST"

        if index_up and (not middle_up) and (not ring_up) and (not pinky_up):
            return "POINT"

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
