import math

class GestureDetector:

    def distancia(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.hypot(x2 - x1, y2 - y1)

    def detectar(self, pontos):

        if len(pontos) != 21:
            return None

        d_palma = self.distancia(pontos[0], pontos[9])

        def dedo_levantado(ponta, base, fator):
            return self.distancia(pontos[ponta], pontos[base]) > d_palma * fator

        indicador = dedo_levantado(8, 5, 0.55)
        medio = dedo_levantado(12, 9, 0.55)
        anelar = dedo_levantado(16, 13, 0.50)
        mindinho = dedo_levantado(20, 17, 0.50)
        polegar = dedo_levantado(4, 2, 0.45)
        
        # ✌
        if indicador and medio and not anelar and not mindinho:
            return "V"

        # 👍
        if polegar and not indicador and not medio and not anelar and not mindinho:
            return "THUMBS_UP"

        # ✋
        if indicador and medio and anelar and mindinho:
            return "OPEN_HAND"

        # 👊
        if not indicador and not medio and not anelar and not mindinho:
            return "FIST"

        # ☝
        if indicador and not medio and not anelar and not mindinho:
            return "POINT"

        # 🤘
        if indicador and mindinho and not medio and not anelar:
            return "ROCK"

        return None