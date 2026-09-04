"""Testes do GestureDetector com landmarks sintéticos — sem webcam, sem MediaPipe."""

import pytest

from core.gesture_detector import GestureDetector
from tests.maos_sinteticas import mao, mao_com, rotacionar


@pytest.fixture
def detector():
    return GestureDetector()


# (nome esperado, kwargs para montar a mão)
GESTOS = [
    ("THUMBS_UP", dict(polegar="aberto_cima")),
    ("THUMBS_DOWN", dict(polegar="aberto_baixo")),
    ("FIST", dict(polegar="fechado")),
    ("OPEN_HAND", dict(indicador=True, medio=True, anelar=True, minimo=True, polegar="aberto_lado")),
    ("FOUR", dict(indicador=True, medio=True, anelar=True, minimo=True, polegar="fechado")),
    ("THREE", dict(indicador=True, medio=True, anelar=True, polegar="fechado")),
    ("V", dict(indicador=True, medio=True, polegar="fechado")),
    ("ROCK", dict(indicador=True, minimo=True, polegar="fechado")),
    ("CALL_ME", dict(minimo=True, polegar="aberto_lado")),
    ("Dedo do Meio", dict(medio=True, polegar="fechado")),
    ("POINT", dict(indicador=True, polegar="fechado")),
    ("Arminha", dict(indicador=True, polegar="aberto_lado")),
]


@pytest.mark.parametrize("esperado,forma", GESTOS, ids=[nome for nome, _ in GESTOS])
def test_detecta_cada_gesto(detector, esperado, forma):
    assert detector.detectar(mao(**forma)) == esperado


def test_escoteiro_quando_pontas_se_tocam(detector):
    """Escoteiro é um V com indicador e médio encostados (dist < palm_size * 0.25)."""
    v = mao(indicador=True, medio=True, polegar="fechado")
    assert detector.detectar(v) == "V"

    escoteiro = mao_com(v, {8: (85, 255)})
    assert detector.detectar(escoteiro) == "Escoteiro"


def test_ok_sign_com_polegar_encostando_no_indicador(detector):
    """OK exige indicador dobrado, polegar colado nele e os outros três estendidos."""
    base = mao(medio=True, anelar=True, minimo=True, polegar="fechado")
    ok = mao_com(base, {4: (95, 355)})
    assert detector.detectar(ok) == "OK_SIGN"


class TestEntradaInvalida:
    def test_lista_vazia_retorna_none(self, detector):
        assert detector.detectar([]) is None

    def test_menos_de_21_pontos_retorna_none(self, detector):
        assert detector.detectar([(0, 0)] * 20) is None

    def test_mais_de_21_pontos_retorna_none(self, detector):
        """Duas mãos concatenadas (42 pontos) devem ser rejeitadas, não interpretadas.

        Guarda o pitfall CRITICAL-01: antes da API multi-mão, habilitar 2 mãos fazia
        `processar()` devolver uma lista achatada de 42 pontos e a detecção morria em
        silêncio.
        """
        assert detector.detectar([(0, 0)] * 42) is None


class TestFronteirasFrageis:
    """Pares que diferem por um único booleano — documentam onde a detecção é sensível.

    Se alguém mexer nos limiares do detector, estes testes dizem qual par quebrou.
    """

    def test_arminha_e_point_diferem_so_pelo_polegar(self, detector):
        assert detector.detectar(mao(indicador=True, polegar="fechado")) == "POINT"
        assert detector.detectar(mao(indicador=True, polegar="aberto_lado")) == "Arminha"

    def test_open_hand_e_four_diferem_so_pelo_polegar(self, detector):
        quatro_dedos = dict(indicador=True, medio=True, anelar=True, minimo=True)
        assert detector.detectar(mao(**quatro_dedos, polegar="fechado")) == "FOUR"
        assert detector.detectar(mao(**quatro_dedos, polegar="aberto_lado")) == "OPEN_HAND"

    def test_thumbs_up_e_down_diferem_so_pela_direcao_do_polegar(self, detector):
        """Mesma forma de mão; o que separa é para onde o polegar aponta (D-28)."""
        assert detector.detectar(mao(polegar="aberto_cima")) == "THUMBS_UP"
        assert detector.detectar(mao(polegar="aberto_baixo")) == "THUMBS_DOWN"

    def test_mao_fechada_com_polegar_aberto_de_lado_nao_dispara_nada(self, detector):
        """Pose ambígua devolve None — nem joinha, nem deslike, nem punho.

        FIST exige `not thumb_open`, e THUMBS_UP/DOWN exigem que a ponta do polegar
        esteja claramente acima ou abaixo. Com o polegar aberto na horizontal nenhum
        dos três casa, e o detector prefere não classificar a chutar.

        Comportamento correto para um app de live: um gesto ambíguo não deve trocar
        a cena. Se algum dia isso virar FIST, foi mudança deliberada — não deixe
        acontecer por acidente.
        """
        assert detector.detectar(mao(polegar="aberto_lado")) is None

    def test_punho_exige_polegar_recolhido(self, detector):
        assert detector.detectar(mao(polegar="fechado")) == "FIST"


class TestRotacao:
    """Tolerância do detector a inclinação da mão. Ver D-28 e .planning/active/B-06.md.

    Medição que motivou isto: com a regra antiga (comparação de coordenada Y crua), um
    joinha inclinado ~70° era detectado como DESLIKE — o gesto oposto, sem sinal de
    ambiguidade nenhum.
    """

    GESTOS_DE_DEDO = [
        ("FIST", dict(polegar="fechado")),
        ("V", dict(indicador=True, medio=True, polegar="fechado")),
        ("POINT", dict(indicador=True, polegar="fechado")),
        ("CALL_ME", dict(minimo=True, polegar="aberto_lado")),
        ("OPEN_HAND", dict(indicador=True, medio=True, anelar=True, minimo=True, polegar="aberto_lado")),
    ]

    @pytest.mark.parametrize(
        "esperado,forma", GESTOS_DE_DEDO, ids=[n for n, _ in GESTOS_DE_DEDO]
    )
    @pytest.mark.parametrize("graus", [-180, -90, -45, 45, 90, 180])
    def test_gestos_de_dedo_sao_invariantes_a_rotacao(self, detector, esperado, forma, graus):
        """`_finger_extended` mede distância ao pulso, que é radial — não muda com rotação.

        Isto corrige uma suposição errada do backlog original, que dizia que estes gestos
        eram frágeis a rotação. Não são.
        """
        girada = rotacionar(mao(**forma), graus)
        assert detector.detectar(girada) == esperado

    @pytest.mark.parametrize("graus", [-10, 0, 15, 45, 70])
    def test_joinha_aguenta_inclinacao_moderada(self, detector, graus):
        girada = rotacionar(mao(polegar="aberto_cima"), graus)
        assert detector.detectar(girada) == "THUMBS_UP"

    def test_polegar_apontando_para_cima_e_para_o_lado_nao_e_joinha(self, detector):
        """Caso real reportado com foto (2026-09-04). Ver D-36.

        Mão fechada com o polegar saindo na diagonal, a ~50° da vertical. Com a
        tolerância antiga de 60° isso passava como joinha; o usuário não considera aquilo
        um joinha, e é uma pose fácil de fazer sem querer com a mão relaxada ao lado do
        rosto.

        O polegar está no PLANO da imagem (projeção longa), então o gate de comprimento
        do D-35 não pega este caso — quem resolve é a tolerância angular.
        """
        base = mao(polegar="aberto_cima")
        # a fixture já sai a ~33° da vertical; girar -20 afasta mais, chegando a ~53°
        diagonal = rotacionar(base, -20)

        angulo = detector.angulo_do_polegar(diagonal)
        assert 45 < angulo < 60, f"a pose de teste precisa cair na faixa disputada: {angulo:.0f}°"
        assert detector.detectar(diagonal) is None

    def test_inverter_joinha_exige_atravessar_a_zona_morta(self, detector):
        """A garantia central do D-28: não existe salto direto de joinha para deslike.

        Varre a rotação de 1 em 1 grau. Entre o último THUMBS_UP e o primeiro
        THUMBS_DOWN tem de haver pelo menos um ângulo devolvendo None — caso contrário
        um tremor de mão poderia trocar para a cena oposta.
        """
        base = mao(polegar="aberto_cima")
        leitura = [detector.detectar(rotacionar(base, g)) for g in range(-180, 181)]

        for anterior, atual in zip(leitura, leitura[1:]):
            assert not (anterior == "THUMBS_UP" and atual == "THUMBS_DOWN")
            assert not (anterior == "THUMBS_DOWN" and atual == "THUMBS_UP")

    def test_polegar_na_horizontal_fica_na_zona_morta(self, detector):
        """90° da vertical não é nem joinha nem deslike — é ambíguo, e ambíguo não dispara."""
        assert detector.detectar(mao(polegar="aberto_lado")) is None

    def test_zona_morta_e_simetrica(self, detector):
        """Girar +X e -X a partir da horizontal tem de dar o mesmo veredito.

        A regra antiga era assimétrica de nascença (THUMBS_UP sobrevivia -25/+115 e
        THUMBS_DOWN -115/+45), porque a fronteira era efeito colateral da posição dos
        pontos 3 e 5, não uma decisão.
        """
        horizontal = mao(polegar="aberto_lado")
        for delta in (10, 20, 25):
            assert detector.detectar(rotacionar(horizontal, delta)) == detector.detectar(
                rotacionar(horizontal, -delta)
            )


class TestPolegarEmProfundidade:
    """O ângulo do polegar só vale se ele estiver de frente para a câmera. Ver D-35.

    `angulo_do_polegar` mede apenas X/Y. Um polegar apontando para a câmera ou para longe
    dela projeta um vetor curto, cuja direção é quase ruído — mas caía dentro da tolerância
    angular e virava joinha. Relatado como "joinha de lado, com o dedão apontando para
    trás".
    """

    # Ponta a ~44% do palm_size da base do polegar: aberto, mas encurtado na projeção.
    # Antes deste gate, isto era classificado como THUMBS_DOWN.
    PONTA_EM_PROFUNDIDADE = (40, 391)

    def test_polegar_encurtado_nao_vira_gesto(self, detector):
        forma = mao_com(mao(polegar="aberto_cima"), {4: self.PONTA_EM_PROFUNDIDADE})
        assert detector.detectar(forma) is None

    def test_polegar_de_frente_continua_valendo(self, detector):
        """A correção não pode custar o caso normal — este é o joinha de sempre."""
        assert detector.detectar(mao(polegar="aberto_cima")) == "THUMBS_UP"
        assert detector.detectar(mao(polegar="aberto_baixo")) == "THUMBS_DOWN"

    def test_o_gate_e_invariante_a_rotacao(self, detector):
        """Comprimento é distância, e distância não muda com rotação.

        Garante que o gate do D-35 não reintroduz a fragilidade que o D-28 removeu: um
        joinha inclinado continua sendo joinha dentro da tolerância angular.
        """
        for graus in (-10, 0, 20, 45):
            girada = rotacionar(mao(polegar="aberto_cima"), graus)
            assert detector.detectar(girada) == "THUMBS_UP"

    def test_punho_nao_e_afetado(self, detector):
        """FIST não depende do ângulo do polegar, só de ele estar recolhido."""
        assert detector.detectar(mao(polegar="fechado")) == "FIST"


class TestLimiarDeDedoEstendido:
    """Fixa o limiar `dist_tip > dist_mcp * 1.2` de `_finger_extended`.

    Os outros testes usam poses extremas (ponta a ~150px do pulso quando estendida,
    ~57px quando dobrada) e passariam com quase qualquer limiar. Estes exercitam a
    fronteira: a base do indicador está a ~95px do pulso, então o corte fica em ~114px.
    """

    # ~105px do pulso: acima de 1.05x (~100px), abaixo de 1.2x (~114px)
    PONTA_AMBIGUA = (67, 300)
    # ~123px do pulso: acima de 1.2x
    PONTA_ESTENDIDA = (70, 280)

    def test_dedo_meio_esticado_ainda_conta_como_dobrado(self, detector):
        """Um indicador parcialmente esticado não vira POINT.

        Se este teste virar POINT, o limiar foi afrouxado — e gestos vão disparar com
        a mão relaxada, que é justamente o que o hold_time e o stability monitor
        tentam evitar.
        """
        forma = mao_com(mao(polegar="fechado"), {8: self.PONTA_AMBIGUA})
        assert detector.detectar(forma) == "FIST"

    def test_dedo_claramente_esticado_conta_como_estendido(self, detector):
        forma = mao_com(mao(polegar="fechado"), {8: self.PONTA_ESTENDIDA})
        assert detector.detectar(forma) == "POINT"
