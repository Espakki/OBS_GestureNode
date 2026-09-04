"""Construtor de landmarks sintéticos para testar o GestureDetector sem webcam.

Reproduz a geometria que o MediaPipe entrega: 21 pontos (px, py) em coordenadas de
imagem, onde **y cresce para baixo**. A mão modelada aponta para cima, com o pulso em
(100, 400) e a base do dedo médio em (100, 300) — o que dá `palm_size` = 100 e torna os
limiares do detector fáceis de raciocinar:

- dedo estendido: `dist(pulso, ponta) > dist(pulso, base) * 1.2`
- polegar aberto: `dist(ponta_polegar, base_indicador) > palm_size * 0.6` (ou seja, > 60)
- polegar/indicador juntos: `dist(4, 8) < palm_size * 0.3` (ou seja, < 30)

Índices do MediaPipe: 0 pulso · 1-4 polegar · 5-8 indicador · 9-12 médio ·
13-16 anelar · 17-20 mínimo. Em cada dedo a ordem é base → ponta.
"""

PULSO = (100, 400)

# Base (MCP) de cada dedo, indexada pelo índice do landmark
_BASES = {5: (70, 310), 9: (100, 300), 13: (130, 310), 17: (160, 320)}

# Ponta (TIP) de cada dedo nos dois estados. Estendida fica bem acima do limiar de 1.2x;
# dobrada fica junto à palma, bem abaixo dele.
_PONTAS = {
    8: {"estendido": (52, 256), "dobrado": (85, 345)},
    12: {"estendido": (100, 250), "dobrado": (100, 345)},
    16: {"estendido": (148, 256), "dobrado": (115, 345)},
    20: {"estendido": (196, 272), "dobrado": (130, 350)},
}

# Polegar: (ponta_4, articulacao_3) por estado.
# "aberto_cima"  -> thumb_open e y4 < y3 e y4 < y5  => THUMBS_UP
# "aberto_baixo" -> thumb_open e y4 > y3 e y4 > y5  => THUMBS_DOWN
# "aberto_lado"  -> thumb_open mas nem up nem down  => só "aberto"
# "fechado"      -> encostado na base do indicador  => not thumb_open
_POLEGAR = {
    "aberto_cima": ((10, 280), (30, 320)),
    "aberto_baixo": ((10, 380), (30, 340)),
    "aberto_lado": ((5, 320), (35, 340)),
    "fechado": ((60, 320), (65, 340)),
}

_DEDOS = {"indicador": 8, "medio": 12, "anelar": 16, "minimo": 20}


def mao(indicador=False, medio=False, anelar=False, minimo=False, polegar="fechado"):
    """Monta os 21 landmarks de uma mão.

    Cada dedo é um bool (True = estendido). `polegar` é uma das chaves de `_POLEGAR`.
    Retorna list[tuple[int, int]] com 21 posições, pronta para `GestureDetector.detectar`.
    """
    if polegar not in _POLEGAR:
        raise ValueError(f"polegar inválido: {polegar!r}. Use um de {sorted(_POLEGAR)}")

    pontos = [(0, 0)] * 21
    pontos[0] = PULSO

    ponta_polegar, articulacao = _POLEGAR[polegar]
    pontos[1] = (75, 375)
    pontos[2] = (55, 350)
    pontos[3] = articulacao
    pontos[4] = ponta_polegar

    estados = {
        8: indicador,
        12: medio,
        16: anelar,
        20: minimo,
    }

    for idx_ponta, estendido in estados.items():
        idx_base = idx_ponta - 3
        base = _BASES[idx_base]
        ponta = _PONTAS[idx_ponta]["estendido" if estendido else "dobrado"]

        pontos[idx_base] = base
        pontos[idx_ponta] = ponta
        # Falanges intermediárias interpoladas — o detector não as usa, mas mantém a
        # estrutura coerente para quem for depurar visualizando os pontos.
        pontos[idx_base + 1] = _entre(base, ponta, 1 / 3)
        pontos[idx_base + 2] = _entre(base, ponta, 2 / 3)

    return pontos


def _entre(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t))


def mao_com(pontos, substituicoes):
    """Copia `pontos` trocando landmarks específicos: `mao_com(p, {8: (52, 256)})`."""
    novos = list(pontos)
    for idx, valor in substituicoes.items():
        novos[idx] = valor
    return novos
