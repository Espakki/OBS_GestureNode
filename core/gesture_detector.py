import math


# Quanto o polegar pode desviar da vertical da imagem e ainda contar como joinha/deslike.
# A zona morta entre os dois é 180 - 2*TOLERANCIA (60° com o valor atual): para um joinha
# virar deslike seria preciso atravessar essa faixa inteira, e no meio dela o detector não
# devolve gesto nenhum. Ver D-28.
#
# Joinha e deslike são a MESMA forma de mão girada 180°, então a orientação absoluta é
# informação essencial aqui — não dá para tornar isso invariante a rotação sem tornar os
# dois indistinguíveis. O que dá é fazer a fronteira ser explícita e simétrica.
TOLERANCIA_POLEGAR_GRAUS = 60

# Comprimento mínimo do polegar projetado, como fração do `palm_size`.
#
# O ângulo acima só enxerga X/Y. Um polegar apontando PARA a câmera ou para longe dela
# projeta um vetor curto, e a direção desse vetor curto é quase ruído — mas ainda podia
# cair dentro da tolerância angular e virar joinha. Era o caso do "joinha de lado, com o
# dedão apontando para trás".
#
# Medido nas mãos sintéticas: joinha e deslike de frente dão 0.83; um polegar em
# profundidade dá 0.44. O corte em 0.55 rejeita o segundo com folga e aceita o primeiro
# com muita. Em termos de rotação em profundidade, equivale a exigir que a mão não esteja
# mais de ~48° girada para o lado. Ver D-35.
COMPRIMENTO_MINIMO_POLEGAR = 0.55


class GestureDetector:

    def _angulo_do_polegar(self, pontos):
        """Ângulo entre o polegar e a vertical da imagem, em graus [0, 180].

        0 = apontando para cima na tela, 180 = para baixo, 90 = na horizontal.
        Usa o vetor da base do polegar (ponto 2) até a ponta (ponto 4), que é mais
        estável que a última falange sozinha.
        """
        (bx, by), (tx, ty) = pontos[2], pontos[4]
        dx, dy = tx - bx, ty - by

        if dx == 0 and dy == 0:
            return 90.0  # degenerado: trata como horizontal, não classifica

        # -dy porque y cresce para baixo na imagem
        return abs(math.degrees(math.atan2(dx, -dy)))

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

        # Ângulo explícito em vez de comparar coordenadas Y cruas: a regra antiga tinha
        # fronteira assimétrica e fazia joinha virar deslike a ~70° de inclinação, sem
        # passar por zona morta. Ver D-28.
        angulo_polegar = self._angulo_do_polegar(pontos)

        # O ângulo só é confiável se o polegar estiver razoavelmente de frente. Muito
        # encurtado na projeção significa apontando na profundidade, e aí a direção X/Y
        # não diz nada. Ver D-35.
        comprimento_polegar = self.distancia(pontos[2], pontos[4])
        polegar_de_frente = comprimento_polegar > (palm_size * COMPRIMENTO_MINIMO_POLEGAR)

        thumb_up = thumb_open and polegar_de_frente and angulo_polegar <= TOLERANCIA_POLEGAR_GRAUS
        thumb_down = (
            thumb_open
            and polegar_de_frente
            and angulo_polegar >= (180 - TOLERANCIA_POLEGAR_GRAUS)
        )

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