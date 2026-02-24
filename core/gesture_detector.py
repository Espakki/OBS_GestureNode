import math

class GestureDetector:

    def distancia(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.hypot(x2 - x1, y2 - y1)

    def detectar(self, pontos):

        if len(pontos) != 21:
            return None

        d_indicador = self.distancia(pontos[8], pontos[5])
        d_medio = self.distancia(pontos[12], pontos[9])
        d_palma = self.distancia(pontos[0], pontos[9])

        indicador = d_indicador > d_palma * 0.55
        medio = d_medio > d_palma * 0.55

        # gesto V
        if indicador and medio:
            return "V"

        return None